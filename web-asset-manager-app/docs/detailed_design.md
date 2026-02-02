# 詳細設計書（Web Asset Manager）

## 1. モジュール詳細
### 1.1 app.py
- 画面ルーティング（HTML）とAPI（JSON）の提供
- 監査ログの追記
- 位置保存と割当操作の受け口

### 1.2 services.py
- `AssetService`: デバイス/ライセンスのCRUD
- `ConfigService`: 構成CRUD、割当/移動、付帯情報取得

### 1.3 repositories.py
- 各テーブルへのSQLアクセス
- `AuditRepository`: 監査ログの追記/参照（ハッシュチェーン）

### 1.4 db.py
- スキーマ生成
- サンプルデータ投入

### 1.5 templates/static
- 画面テンプレート、ドラッグ&ドロップ、タブ切替、並び替え

## 2. データベース設計
### 2.1 テーブル定義（主要列）
- **devices**: device_id(PK), asset_no(UNIQUE), display_name, device_type, model, version, state, note
- **licenses**: license_id(PK), license_no, name, license_key, state, note
- **configurations**: config_id(PK), config_no, name, note, created_at, updated_at
- **config_devices**: config_id(FK), device_id(FK), PK(config_id, device_id)
- **config_licenses**: config_id(FK), license_id(FK, UNIQUE), note
- **config_positions**: config_id(PK), x, y, hidden
- **audit_logs**: audit_id(PK), config_id, action, actor, details_json, created_at, prev_hash, entry_hash

### 2.2 関連
- configurations 1..n config_devices / config_licenses
- configurations 1..1 config_positions
- configurations 1..n audit_logs

## 3. API詳細
### 3.1 構成系
- **POST /configurations**
  - 入力: `name`, `note`
  - 出力: 303リダイレクト
  - 監査: `config.create`

- **POST /configurations/{id}/edit**
  - 入力: `name`, `note`
  - 出力: 303リダイレクト
  - 監査: `config.update`（before/after）

- **POST /configurations/{id}/delete**
  - 出力: 303リダイレクト
  - 監査: `config.delete`（割当一覧を含む）

- **POST /api/configs/{id}/assign**
  - 入力(JSON): `asset_type`(device|license), `asset_id`, `source_config_id`
  - 出力: `{status: ok}`
  - 例外: 409（他構成に割当済み）
  - 監査: assign/move

- **POST /api/configs/{id}/position**
  - 入力(JSON): `x`, `y`
  - 出力: `{status: ok}`
  - 監査: `config.position`

- **GET /api/summary**
  - 出力: `{devices, licenses, configs}`

- **GET /health**
  - 出力: `{status: ok}`

## 4. 画面・UI挙動
### 4.1 検索/ソート
- 検索パラメータ: `device_q`, `license_q`, `config_q`
- ソートパラメータ: `*_sort`, `*_dir`

### 4.2 ドラッグ&ドロップ
- 画面上の資産タグをドラッグ
- 構成カードのドロップ領域に投入
- API `/api/configs/{id}/assign` を呼び出し
- 成功後に画面反映

### 4.3 カード配置
- 構成カードをキャンバス上でドラッグ
- API `/api/configs/{id}/position` を呼び出し
- 起動時は保存位置を復元し、未保存はグリッド配置

### 4.4 タブ
- 日本/アメリカのタブでカード/一覧を表示切替
- 初期は日本タブ

## 5. 監査ログ設計
### 5.1 ハッシュチェーン
監査ログのハッシュは以下で算出する。

$$
H = SHA256(created\_at | config\_id | action | actor | details\_json | prev\_hash)
$$

- `prev_hash` は同一構成内の直前ログの `entry_hash`
- 変更履歴の改ざん検知を目的とする

## 6. 処理フロー
### 6.1 構成作成
1. 画面入力を受領
2. configurationsに追加
3. `config.create` を監査ログへ記録
4. 一覧へリダイレクト

### 6.2 割当/移動
1. ドラッグ&ドロップでAPI呼び出し
2. 既存割当を確認
3. assign/moveを実行
4. `config.device.assign` / `config.device.move` を記録

### 6.3 位置保存
1. カード移動後に位置保存APIを呼び出し
2. config_positionsに保存
3. `config.position` を記録

### 6.4 構成削除
1. 対象構成/割当一覧を取得
2. `config.delete` を記録
3. 対象構成を削除
