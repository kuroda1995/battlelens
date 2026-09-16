# BattleLens(仮称)

対戦ゲームのパーティ構築・分析を行う個人開発ツールです。学習目的・ポートフォリオとして、学校で習った技術スタック(React / TypeScript / Vite / Tailwind CSS / Java / Spring Boot / Gradle / PostgreSQL)を意図的に使わず、別の技術スタックで一からアプリケーションを構築し、AWSにデプロイしています。

> **免責事項**: 本アプリは個人が趣味・学習目的で作成した非公式のファンツールであり、Nintendo / Game Freak / The Pokémon Company とは一切関係ありません。ゲーム内の種族名・技名等のデータは [PokéAPI](https://pokeapi.co/) を通じて取得しており、公式のロゴ・画像・キャラクターアートは使用していません。実装しているのは努力値・個体値・タイプ相性などの「ゲームメカニクス(数式・ルール)」であり、これらは著作物ではなく事実・アイデアの領域として扱っています。

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

## リポジトリ構成

```
frontend/   Svelte + Rollup によるSPA
backend/    FastAPI + Poetry によるREST API
infra/      AWS CDK (Python) によるインフラ定義
```

## 開発フェーズ

- **Phase 0**: プロジェクト土台構築(このコミット)
- **Phase 1**: パーティ構築・保存機能のMVPをAWSにデプロイ(このコミット)
- **Phase 2**: ダメージ計算機
- **Phase 3**: 相手の行動予測・簡易勝率推定
- **Phase 4**: Amazon Cognitoによるログイン、対戦ログ保存・分析、CI/CD
- **Phase 5**: 勝率予測モデルの高度化、監視、独自ドメイン

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

## ライセンス

自作コード部分は [MIT License](./LICENSE) です。ゲーム内データ・名称等の権利は各権利者に帰属します。
