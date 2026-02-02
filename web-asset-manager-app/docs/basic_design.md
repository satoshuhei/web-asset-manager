# 基本設計書（Web Asset Manager）

## 1. システム概要
デバイス/ライセンス資産を構成（Configuration）に割当し、配置と履歴を可視化するWebアプリ。

## 2. アーキテクチャ
- **プレゼンテーション層**: Jinja2テンプレート + 静的JS/CSS
- **API/Web層**: FastAPI（HTML/JSON）
- **サービス層**: 画面・APIのユースケースを抽象化
- **リポジトリ層**: SQLiteへのCRUD

## 3. 構成要素
- **app.py**: ルーティング・画面/JSON応答
- **src/wam/services.py**: 主要ユースケース
- **src/wam/repositories.py**: 永続化アクセス
- **src/wam/db.py**: スキーマ/初期データ
- **web/templates**: 画面テンプレート
- **web/static**: UIスクリプト/スタイル

## 4. データモデル概要
- **Device**: device_id, asset_no, display_name, device_type, model, version, state, note
- **License**: license_id, license_no, name, license_key, state, note
- **Configuration**: config_id, config_no, name, note, created_at, updated_at
- **ConfigDevice**: config_id, device_id
- **ConfigLicense**: config_id, license_id, note
- **ConfigPosition**: config_id, x, y, hidden
- **AuditLog**: audit_id, config_id, action, actor, details_json, created_at, prev_hash, entry_hash

## 5. 画面設計（概要）
### 5.1 Assets
- デバイス/ライセンス件数の要約カード
- 一覧画面への遷移

### 5.2 デバイス一覧
- 検索・ソート・CRUD操作
- Redmine風テーブル

### 5.3 ライセンス一覧
- 検索・ソート・CRUD操作
- Redmine風テーブル

### 5.4 構成一覧
- 一覧（上段）: 件数/タグ/作成日/更新日
- タブ: 日本/アメリカ
- 右側: 未割当デバイス/ライセンス
- キャンバス: 構成カード配置・ドラッグ

### 5.5 構成詳細
- 構成情報
- 割当デバイス/ライセンス一覧
- 変更履歴（監査ログ）

## 6. API設計（概要）
- **GET /assets**: 資産トップ
- **GET /assets/devices, /assets/licenses**: 一覧
- **POST /assets/devices, /assets/licenses**: 作成
- **POST /assets/*/{id}/edit**: 更新
- **POST /assets/*/{id}/delete**: 削除
- **GET /configurations**: 構成一覧
- **POST /configurations**: 作成
- **POST /configurations/{id}/edit**: 更新
- **POST /configurations/{id}/delete**: 削除
- **POST /api/configs/{id}/assign**: デバイス/ライセンス割当
- **POST /api/configs/{id}/position**: カード位置保存
- **GET /api/summary**: 件数サマリ
- **GET /health**: 稼働確認

## 7. 例外・エラー
- 409: 既に割当済みの資産を別構成に割当する場合
- 400: 不正な資産種別の指定
- 404相当: 取得対象が存在しない場合（ValueError）

## 8. 監査ログ
- 構成単位で操作履歴を記録
- 前後ハッシュで改ざん検知
- 構成詳細で最大200件表示
