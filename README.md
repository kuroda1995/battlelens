# BattleLens(仮称)

![Svelte](https://img.shields.io/badge/Svelte-FF3E00?style=flat&logo=svelte&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat&logo=mysql&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-232F3E?style=flat&logo=amazonaws&logoColor=white)
![AWS CDK](https://img.shields.io/badge/IaC-AWS%20CDK-blueviolet?style=flat)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

対戦ゲームのパーティ構築・ダメージ計算を支援する個人開発ツールです。学校で習った技術スタック(React / TypeScript / Vite / Tailwind CSS / Java / Spring Boot / Gradle / PostgreSQL)を意図的に使わず、代替技術で一からアプリケーションを設計・実装し、AWS上に実際にデプロイしています。

> **免責事項**: 本アプリは個人が趣味・学習目的で作成した非公式のファンツールであり、Nintendo / Game Freak / The Pokémon Company とは一切関係ありません。ゲーム内の種族名・技名等のデータは [PokéAPI](https://pokeapi.co/) を通じて取得しており、公式のロゴ・画像・キャラクターアートは使用していません。実装しているのは努力値・個体値・タイプ相性などの「ゲームメカニクス(数式・ルール)」であり、これらは著作物ではなく事実・アイデアの領域として扱っています。

## デモ

| | |
|---|---|
| 🎥 デモ動画 | [Google Drive で視聴する](https://drive.google.com/file/d/1o5YH5x_mMRnfXZJtdWfRdvp1tDcj7BQU/view?usp=drive_link) |
| 🌐 本番環境(AWS) | https://d2lvrrryjxvijh.cloudfront.net |

> 本番環境は個人検証用のAWSアカウント上で稼働しています。コスト管理のため、閲覧時に停止している場合はデモ動画をご覧ください。

## 作成背景

対戦ポケモンでは、種族値・努力値・性格・技構成の組み合わせによって実数値やダメージ量が大きく変わり、パーティ構築のたびに手計算や暗算に頼ると時間がかかり、ミスも起きやすいという課題があります。この分析作業を効率化し、対戦の質を高める助けになるツールとして BattleLens を開発しました。

また、学校の課題としては「指定技術を使わない」という制約があったため、単に動くものを作るのではなく、**なぜその技術を選んだのかを自分の言葉で説明できること**を最優先に技術選定・設計を行っています。

## 見てほしいポイント(こだわり)

- **PokéAPIへの非同期並列リクエスト**: 種族名・技・特性の日本語名解決など、多数の外部API呼び出しが必要な処理では `asyncio.gather` と `asyncio.Semaphore` を組み合わせ、同時実行数を制御しながら並列取得することでレスポンスを高速化しています([`app/routers/species.py`](backend/app/routers/species.py), [`app/pokeapi_client.py`](backend/app/pokeapi_client.py))。
- **ゲーム独自仕様のリバースエンジニアリング**: 本タイトルの努力値システムは、公開資料がなく仕様が非公開だったため、実機のステータス実測値から数式を逆算し、単体テストで実測値と完全一致することを検証した上で実装しています([`app/calculations/stats.py`](backend/app/calculations/stats.py), [`backend/tests/test_stats.py`](backend/tests/test_stats.py))。
- **React/TypeScriptではなくSvelte + JSDocを採用**: 仮想DOMを使わずコンパイル時にDOM更新コードを生成するSvelteの設計思想を実践し、TypeScriptを使わずJSDocのみで最小限の型ヒントを得る構成を検証しています。
- **SSH鍵レスなインフラ運用**: EC2への接続はSSH鍵・22番ポート開放を一切行わず、AWS Systems Manager Session Manager経由のみで運用しています。RDSも分離サブネットに配置し、EC2からの3306番ポート接続のみを許可しています。

## 苦労した点と解決策

- **外部API(PokéAPI)のレイテンシとレート制限**: 種族・技・特性の日本語名を都度取得すると初回アクセスが遅くなる課題があったため、`asyncio.Semaphore`で同時接続数を制限しつつ並列化し、取得済みデータをプロセス内キャッシュすることで2回目以降のレスポンスを高速化しました。
- **禁止技術の制約下での設計思想の理解**: React/Vite/Tailwind/Spring Boot/Gradle/PostgreSQLを使わないという制約の中で、単なる代替ツールの置き換えに留まらず、Svelteのコンパイル最適化、FastAPIの非同期処理、Poetryの依存解決の仕組みなど、それぞれの設計思想の違いを理解しながら環境構築を行いました(詳細は[技術選定の理由](docs/tech-stack-rationale.md)を参照)。
- **AWS無料利用枠内に収めるためのコスト設計**: 当初はDB認証情報をAWS Secrets Managerで自動管理する設計にしていましたが、個人の学習用プロジェクトを完全に無料枠内へ収めるため、Secrets Manager(無料枠対象外の固定費が発生)をやめ、ローカルにのみ保存するパスワードをEC2起動時に安全に注入する方式に変更しました。同時に、意図せず無料枠を超えた場合に気づけるようAWS Budgetsで予算アラートを設定しています。
- **実デプロイ時に判明したAWS特有の制約への対応**: `cdk deploy`を実際に実行した際、セキュリティグループの説明文にASCII文字以外(日本語)が使えない制約や、CloudFrontのオリジンにIPアドレスを直接指定できない制約に遭遇し、それぞれ英語表記への変更・EC2のパブリックDNS名の利用に修正することで解決しました。

## 技術スタックと選定理由

学校で習った技術の「代替」として、あえて別の技術を採用しています。理由は転職活動の面接で技術選定の意図を説明できるようにするためです。

| 領域 | 選定技術 | 学習済み技術 | 選定理由 |
|---|---|---|---|
| フロントエンドUI | Svelte | React | 仮想DOMを使わずコンパイル時にDOM更新コードを生成する設計思想の違いを理解・説明できる |
| 言語(フロント) | JavaScript + JSDoc | TypeScript | ビルド構成をシンプルに保ちながら、JSDocで最小限の型ヒントを得る設計判断 |
| バンドラ | Rollup | Vite | Svelte公式テンプレート標準のバンドラ。dev serverと一体化したViteと異なり、バンドル設定を自分で組む経験を積むため |
| CSS | 素のCSS + Open Props | Tailwind CSS | ユーティリティクラスに頼らず、CSSカスタムプロパティによるデザイントークン管理とコンポーネントスコープCSSの設計力を示すため |
| バックエンド | Python + FastAPI | Java + Spring Boot | 型ヒント+Pydanticによるバリデーション、非同期対応、軽量さを対比して説明できる |
| 依存関係/ビルド管理 | Poetry | Gradle | Pythonにおける依存解決・lockfile・パッケージングの仕組みを理解するため |
| データベース | Amazon RDS for MySQL | PostgreSQL | 禁止技術の対象外RDBMSとして採用。RDBという枠組みは維持しつつ設計思想の違いを説明できる |
| ORM/マイグレーション | SQLAlchemy + Alembic | (Spring Data JPA + Flyway相当) | Python側でのORM設計とスキーママイグレーション管理の経験 |
| インフラ構築 | AWS CDK (Python) | ー | Infrastructure as Codeの経験。バックエンドと同じ言語で統一 |
| コンピュート | Amazon EC2(素のインスタンス + systemd + Nginx) | ー | サーバー運用(OSセットアップ・プロセス常駐化・リバースプロキシ)の経験 |
| 配信/CDN | Amazon S3 + CloudFront | ー | 静的フロントエンドの配信とAPIへのルーティングをCDN層で統合 |
| ネットワーク | VPC + セキュリティグループ + SSM Session Manager | ー | RDSをプライベート隔離し、SSH鍵管理不要でEC2を運用する設計 |
| コスト管理 | AWS Budgets | ー | 個人検証用途のため、無料利用枠超過に気づけるよう予算アラートを設定 |

## アーキテクチャ

```
利用者 → CloudFront(HTTPS) ─┬─ S3(フロントエンド静的ファイル)
                             └─ /api/* → EC2(FastAPI, Nginx+systemd常駐)
                                            └─ RDS for MySQL(分離サブネット)
```

より詳細な構成・データモデル・API仕様は [要件定義書(docs/requirements.md)](docs/requirements.md) を参照してください。

## リポジトリ構成

```
frontend/   Svelte + Rollup によるSPA
backend/    FastAPI + Poetry によるREST API
infra/      AWS CDK (Python) によるインフラ定義
docs/       要件定義・技術選定理由・品質チェック等のドキュメント
```

## 関連ドキュメント

| ドキュメント | 内容 |
|---|---|
| [docs/requirements.md](docs/requirements.md) | 要件定義書。機能要件・進捗状況・データモデル・API仕様・アーキテクチャ図 |
| [docs/tech-stack-rationale.md](docs/tech-stack-rationale.md) | 技術選定の理由(技術面接向け・詳細版) |
| [docs/tech-stack-rationale-beginner.md](docs/tech-stack-rationale-beginner.md) | 技術選定の理由(未経験者向け・平易な解説版) |
| [docs/quality-checklist.md](docs/quality-checklist.md) | 提出前に実施した品質チェックの内容と結果 |
| [docs/demo-script.md](docs/demo-script.md) | デモ動画の進行台本 |

## 開発フェーズ

- **Phase 0**: プロジェクト土台構築 — ✅ 完了
- **Phase 1**: パーティ構築・保存機能のMVP — ✅ 完了・AWSデプロイ済み
- **Phase 2**: ダメージ計算機 — ✅ 完了・AWSデプロイ済み
- **Phase 3**: 相手の行動予測・簡易勝率推定 — 未着手(要件定義のみ)
- **Phase 4**: Amazon Cognitoによるログイン、対戦ログ保存・分析、CI/CD — 未着手
- **Phase 5**: 勝率予測モデルの高度化、監視、独自ドメイン — 構想段階

## ローカル開発

### バックエンド

```
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

### フロントエンド

```
cd frontend
npm install
npm run dev
```

## デプロイ

```
cd infra
pip install -r requirements.txt
cdk deploy
```

詳細な構成・コスト・運用方法は [infra/README.md](infra/README.md) を参照してください。

## ライセンス

自作コード部分は [MIT License](./LICENSE) です。ゲーム内データ・名称等の権利は各権利者に帰属します。
