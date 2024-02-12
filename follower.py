from flask import Flask, request, jsonify
from DWX_ZeroMQ_Connector_v2_0_1_RC8 import DWX_ZeroMQ_Connector

app = Flask(__name__)
_zmq = DWX_ZeroMQ_Connector()


@app.route("/make-trades", methods=["POST"])
def make_trade():
    trades = request.json

    for ticket, trade_data in trades.items():
        _my_trade = _zmq._generate_default_order_dict()

        _my_trade["_symbol"] = trade_data["_symbol"]
        _my_trade["_lots"] = trade_data["_lots"]
        _my_trade["_type"] = trade_data["_type"]
        _my_trade["_SL"] = trade_data["_SL"]
        _my_trade["_TP"] = trade_data["_TP"]
        _my_trade["_comment"] = trade_data["_comment"]

        try:
            _zmq._DWX_MTX_NEW_TRADE_(_order=_my_trade)
        except Exception as e:
            print(f"Error making trade: {e}")
            return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Trades made successfully"})


@app.route("/close-trades", methods=["POST"])
def close_trades():
    removed_trades = request.json

    for remove_trade in removed_trades:
        try:
            _zmq._DWX_MTX_CLOSE_TRADES_BY_COMMENT_(remove_trade)
        except Exception as e:
            print(f"Error closing trades: {e}")
            return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Trades closed successfully"})


if __name__ == "__main__":
    app.run(debug=True)
