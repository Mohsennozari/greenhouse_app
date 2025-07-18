import os

def list_files(start_path, indent=0):
    """
    نمایش ساختار پوشه‌ها و فایل‌ها به‌صورت درختی
    start_path: مسیر شروع (مثل ریشه پروژه)
    indent: فاصله‌گذاری برای نمایش درختی
    """
    try:
        # گرفتن لیست آیتم‌ها در مسیر
        items = os.listdir(start_path)
        # مرتب‌سازی برای نمایش بهتر
        items.sort()
        
        for item in items:
            item_path = os.path.join(start_path, item)
            # فاصله‌گذاری برای نمایش درختی
            print("  " * indent + f"📁 {item}" if os.path.isdir(item_path) else "  " * indent + f"📄 {item}")
            # اگر پوشه بود، زیرمجموعه‌ها رو هم نمایش بده
            if os.path.isdir(item_path):
                list_files(item_path, indent + 1)
                
    except Exception as e:
        print(f"خطا در خواندن مسیر {start_path}: {str(e)}")

if __name__ == "__main__":
    # مسیر پروژه (می‌تونی تغییرش بدی)
    project_path = r"C:\Users\stockland\OneDrive\New folder\OneDrive\Desktop\greenhouse_app"
    print(f"📂 ساختار پروژه: {project_path}\n")
    list_files(project_path)