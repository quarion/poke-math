"""Run the equation calibration viewer on its local-only default port."""

from tools.equation_calibration.app import create_app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=8092, debug=True, threaded=False)
