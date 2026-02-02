# 起動手順書（別PC向け）

## 1. 前提
- Windows 10/11
- Python 3.12 以上
- Git

## 2. 取得
1. 任意の作業フォルダを作成
2. リポジトリを取得

## 3. 仮想環境の作成
1. 作業フォルダで仮想環境を作成
2. 仮想環境を有効化

## 4. 依存関係のインストール
- `web-asset-manager-app` 配下で実行
- `requirements.txt` がある場合はそれを使用

## 5. 起動
- `web-asset-manager-app` 配下でUvicornを起動
- 例: `python -m uvicorn app:app --host 127.0.0.1 --port 9000`

## 6. アクセス
- ブラウザで `http://127.0.0.1:9000` にアクセス

## 7. 初期データ
- 初回起動時にサンプルデータが自動投入される
- DBファイルは `web-asset-manager-app/data/wam.sqlite3`

## 8. よくある問題
- ポート競合: 別のポートに変更して起動
- 起動しない: 依存関係の不足を確認

## 9. 停止
- ターミナルで `Ctrl+C`
