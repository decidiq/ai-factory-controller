import pandas as pd

def run_end_to_end_test():
    print("=== MEMULAI PENGUJIAN END-TO-END (E2E) AI FACTORY CONTROLLER ===")
    
    # 1. Uji Ketersediaan Modul Utama
    modules_to_test = [
        "fc.ui.dashboard",
        "fc.ui.production_analysis",
        "fc.ui.cost_analysis",
        "fc.ui.multi_plant",
        "fc.ui.ai_factory_os",
        "fc.ui.multi_agent_collaboration",
        "fc.ui.executive_report",
        "fc.ui.ai_copilot"
    ]
    
    for mod in modules_to_test:
        try:
            __import__(mod, fromlist=['render'])
            print(f"[OK] Modul {mod} berhasil dimuat.")
        except Exception as e:
            print(f"[GAGAL] Modul {mod} mengalami error: {e}")

    # 2. Uji Impor Pipeline & Variabel Data Utama dari app.py / pipeline
    try:
        import app
        print("[OK] Modul utama app berhasil dimuat.")
        if hasattr(app, "ds"):
            print("[OK] Objek data 'ds' terdeteksi aktif.")
        else:
            print("[PERINGATAN] Objek 'ds' tidak ditemukan secara langsung di app.")
    except Exception as e:
        print(f"[CATATAN] Impor app untuk tes: {e}")

    print("=== PENGUJIAN END-TO-END SELESAI ===")

if __name__ == "__main__":
    run_end_to_end_test()