# infra/ — AWS CDK (Python)

BattleLensのAWSインフラをコードで定義するプロジェクト。`backend/`・`frontend/`のビルド成果物を実際にAWS上で動かすための構成一式(VPC・EC2・RDS・S3・CloudFront)をここで管理する。

## 構成

```
利用者 → CloudFront(HTTPS) ─┬─ S3(フロントエンド静的ファイル)
                             └─ /api/* → EC2(FastAPI, Nginx+systemd常駐)
                                            └─ RDS for MySQL(分離サブネット)
```

- EC2への配布は、GitHubがPrivateリポジトリのため `git clone` を使わず、CDKの`Asset`機能で`backend/`をS3経由で配布している。
- DB認証情報はRDS作成時にSecrets Managerへ自動生成させ、EC2のIAMロールに読み取り権限だけを付与している(コードに書かない)。
- EC2へのログインはSSH鍵を使わず、AWS Systems Manager Session Manager経由で行う。

## 事前準備

```
cd infra
python -m venv .venv
.venv/Scripts/activate   # Windows PowerShellの場合: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

AWS CDK CLIが未導入の場合:
```
npm install -g aws-cdk
```

## コマンド

```
cdk synth    # CloudFormationテンプレートを生成するだけ。AWSリソースは一切作られない(安全)
cdk diff     # 現在AWSにあるものとの差分を確認する
cdk bootstrap  # 初回のみ。CDKがアセット(zipファイル等)を置くためのS3バケット等をアカウントに用意する
cdk deploy   # 実際にAWSリソースを作成・更新する(課金が発生する)
cdk destroy  # 作成したリソースを削除する
```

## ⚠️ `cdk deploy` について

`cdk deploy` を実行すると、実際に以下の費用が発生するAWSリソースが作成される。

| リソース | 目安の料金 |
|---|---|
| EC2 (t3.micro) | 数百円〜/月 |
| RDS for MySQL (db.t3.micro, 20GB) | 1,500円前後〜/月 |
| S3 / CloudFront | 使用量に応じてごく少額 |
| Elastic IP | インスタンス起動中は無料 |

不要になったら `cdk destroy` で削除できる(RDSは`RemovalPolicy.DESTROY`設定済みのため、スナップショットを残さず削除される。学習用途のため許容しているが、本番運用ではスナップショットを残す設定に変更すべき)。

初回デプロイはRDSの作成に10分以上かかることがある。

## デプロイ後の確認

```
# CloudFrontのURL・EC2のIP・DBエンドポイントを確認
cdk deploy --outputs-file outputs.json
```

- フロントエンド: `FrontendURL` の値にブラウザでアクセス
- バックエンドのヘルスチェック: `https://<FrontendURL>/api/health`
- EC2への接続(デバッグ用): AWSコンソールの EC2 → 対象インスタンス → 「接続」→ Session Manager
