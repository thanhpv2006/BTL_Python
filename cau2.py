# cau2_api.py
import pandas as pd
from flask import Flask, jsonify

app = Flask(__name__)

try:
    df = pd.read_csv('data/epl_players_25_26.csv')
    df = df.fillna('N/a')
except FileNotFoundError:
    print("Loi: Khong tim thay file data/epl_players_25_26.csv")
    df = pd.DataFrame()

@app.route('/api/player/<string:name>', methods=['GET'])
def get_player_stats(name):
    if df.empty:
        return jsonify({"error": "Du lieu chua san sang"}), 500
        
    player_data = df[df['Player'].str.contains(name, case=False, na=False)]
    
    if not player_data.empty:
        return jsonify(player_data.iloc[0].to_dict()), 200
    else:
        return jsonify({"error": "Khong tim thay cau thu!"}), 404

if __name__ == '__main__':
    print("Server API dang chay...")
    app.run(debug=True, port=5000)