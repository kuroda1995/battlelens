"""BattleLensのAWSインフラ定義(CDK Python)。

構成:
  CloudFront(HTTPS) --- S3(フロントエンド静的ファイル)
                     └─ /api/* --- EC2(FastAPI, Nginx+systemd常駐) --- RDS for MySQL(分離サブネット)

設計上のポイント(docs/tech-stack-rationale.md と対応):
  - RDSは分離サブネットに置き、EC2からのみ3306番ポートで到達可能にする。
  - EC2の運用はSSM Session Manager経由とし、SSH鍵・22番ポート開放を行わない。
  - DBの認証情報はSecrets Managerで自動生成・管理し、コードに直書きしない。
  - NATゲートウェイは使わずコストを抑える(分離サブネットは外向き通信不要)。
"""

import os

from aws_cdk import (
    CfnOutput,
    Duration,
    IgnoreMode,
    RemovalPolicy,
    Stack,
)
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_rds as rds
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_assets as s3_assets
from aws_cdk import aws_s3_deployment as s3_deploy
from constructs import Construct

_INFRA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = os.path.dirname(_INFRA_DIR)


class BattleLensStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ------------------------------------------------------------------
        # ネットワーク: パブリック(EC2用) + 分離(RDS用、外向き通信なし)
        # ------------------------------------------------------------------
        vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )

        app_security_group = ec2.SecurityGroup(
            self, "AppSecurityGroup", vpc=vpc, description="EC2(FastAPI)用SG"
        )
        app_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "CloudFront/検証用にHTTPを許可"
        )

        db_security_group = ec2.SecurityGroup(
            self,
            "DbSecurityGroup",
            vpc=vpc,
            description="RDS用SG。EC2からのみ許可",
            allow_all_outbound=False,
        )
        db_security_group.add_ingress_rule(
            app_security_group, ec2.Port.tcp(3306), "EC2からのMySQL接続のみ許可"
        )

        # ------------------------------------------------------------------
        # RDS for MySQL(分離サブネット・パブリックアクセス不可)
        # 認証情報はSecrets Managerに自動生成させ、コードに書かない。
        # ------------------------------------------------------------------
        database = rds.DatabaseInstance(
            self,
            "Database",
            engine=rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[db_security_group],
            credentials=rds.Credentials.from_generated_secret("battlelens_admin"),
            database_name="battlelens",
            allocated_storage=20,
            publicly_accessible=False,
            multi_az=False,
            backup_retention=Duration.days(0),
            deletion_protection=False,
            # 個人の学習用プロジェクトのため、スタック削除時にDBごと削除される設定にしている。
            # 本番運用では RemovalPolicy.SNAPSHOT / deletion_protection=True を検討する。
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ------------------------------------------------------------------
        # EC2: backend/ ディレクトリをS3経由で配布し、起動時にセットアップする。
        # GitHubがプライベートリポジトリのため git clone を使わず、
        # CDKのAssetの仕組み(ローカル資産を自動でS3にアップロード)を使う。
        # ------------------------------------------------------------------
        backend_asset = s3_assets.Asset(
            self,
            "BackendAsset",
            path=os.path.join(_REPO_ROOT, "backend"),
            ignore_mode=IgnoreMode.GIT,
        )

        app_role = iam.Role(
            self,
            "AppInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                # SSH鍵・22番ポート開放なしでSession Manager経由の運用を可能にする。
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"),
            ],
        )
        backend_asset.grant_read(app_role)
        database.secret.grant_read(app_role)

        with open(os.path.join(_INFRA_DIR, "user_data.sh.template"), encoding="utf-8") as f:
            user_data_script = f.read()

        user_data_script = (
            user_data_script.replace("__ASSET_BUCKET__", backend_asset.s3_bucket_name)
            .replace("__ASSET_KEY__", backend_asset.s3_object_key)
            .replace("__DB_SECRET_ARN__", database.secret.secret_arn)
            .replace("__DB_ENDPOINT__", database.db_instance_endpoint_address)
            .replace("__DB_PORT__", database.db_instance_endpoint_port)
            .replace("__AWS_REGION__", self.region)
        )

        instance = ec2.Instance(
            self,
            "AppInstance",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            security_group=app_security_group,
            role=app_role,
            user_data=ec2.UserData.custom(user_data_script),
        )
        # RDSの作成完了(10分以上かかることがある)を待ってからEC2を起動する。
        instance.node.add_dependency(database)

        # Elastic IPで固定し、インスタンス再起動時にもCloudFrontのオリジンが
        # 変わらないようにする。
        eip = ec2.CfnEIP(self, "AppEip", domain="vpc", instance_id=instance.instance_id)

        # ------------------------------------------------------------------
        # フロントエンド配信: S3(非公開) + CloudFront(OAC経由のみアクセス許可)
        # ------------------------------------------------------------------
        frontend_bucket = s3.Bucket(
            self,
            "FrontendBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(frontend_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            additional_behaviors={
                "/api/*": cloudfront.BehaviorOptions(
                    origin=origins.HttpOrigin(
                        eip.attr_public_ip,
                        protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                ),
            },
        )

        s3_deploy.BucketDeployment(
            self,
            "DeployFrontend",
            sources=[s3_deploy.Source.asset(os.path.join(_REPO_ROOT, "frontend", "public"))],
            destination_bucket=frontend_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
        )

        # ------------------------------------------------------------------
        # 出力
        # ------------------------------------------------------------------
        CfnOutput(self, "FrontendURL", value=f"https://{distribution.distribution_domain_name}")
        CfnOutput(self, "BackendPublicIp", value=eip.attr_public_ip)
        CfnOutput(self, "DatabaseSecretArn", value=database.secret.secret_arn)
        CfnOutput(self, "DatabaseEndpoint", value=database.db_instance_endpoint_address)
