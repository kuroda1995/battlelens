# infra/ — AWS CDK (Python)

BattleLensのAWSインフラをコードで定義するプロジェクト。`backend/`・`frontend/`のビルド成果物を実際にAWS上で動かすための構成一式(VPC・EC2・RDS・S3・CloudFront)をここで管理する。

## 構成

```
利用者 → CloudFront(HTTPS) ─┬─ S3(フロントエンド静的ファイル)
                             └─ /api/* → EC2(FastAPI, Nginx+systemd常駐)
                                            └─ RDS for MySQL(分離サブネット)
```

- EC2への配布は、GitHubがPrivateリポジトリのため `git clone` を使わず、CDKの`Asset`機能で`backend/`をS3経由で配布している。
- DB認証情報は、無料利用枠に完全に収めるためSecrets Managerを使わず(月$0.40程度が対象外だったため)、`infra/.db-password.txt`(gitには含めない・初回`cdk synth`/`cdk deploy`時に自動生成)にのみ保存し、デプロイ時にEC2へ直接渡している。
- EC2へのログインはSSH鍵を使わず、AWS Systems Manager Session Manager経由で行う。
- 意図せず無料枠を超えた場合に気づけるよう、AWS Budgetsで月$5・実績80%到達時にメール通知するアラートを設定している(作成・アラート自体は無料)。

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

`cdk deploy` を実行すると、実際にAWSリソースが作成される。以下は**AWS無料利用枠(新規アカウントの12ヶ月間)に収まる想定**の構成。

| リソース | 無料枠 | この構成 |
|---|---|---|
| EC2 (t3.micro) | 750時間/月(12ヶ月間) | 1台のみ稼働 → 収まる |
| RDS for MySQL (db.t3.micro, 20GB, シングルAZ) | 750時間/月 + ストレージ20GB(12ヶ月間) | 上限ぴったりの構成 → 収まる |
| S3 / CloudFront | 常時無料枠あり | 個人利用の少量アクセスなら収まる |
| Elastic IP | インスタンス起動中は無料 | 起動したままにする限り無料(停止すると課金される点に注意) |

**注意**: 上記はアカウントが無料利用枠の対象(作成から12ヶ月以内、かつ未使用)である場合の想定。対象外のアカウントでは通常料金(EC2数百円〜/月、RDS 1,500円前後〜/月)が発生する。AWSコンソールの「請求とコスト管理」→「無料利用枠」で事前に確認すること。

意図せず無料枠を超えた場合に気づけるよう、月$5・実績80%到達時にメール通知するAWS Budgetsのアラートを設定済み(`kuromaru.yurulife@gmail.com` 宛)。

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
