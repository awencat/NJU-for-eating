"""
清理过时的文档文件
只保留核心文档:
- README.md
- DEVELOPER_GUIDE.md
- PPT_PRESENTATION_OUTLINE.md
- UPDATE_COORDS_GUIDE.md
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 要保留的文件
KEEP_FILES = {
    'README.md',
    'DEVELOPER_GUIDE.md',
    'PPT_PRESENTATION_OUTLINE.md',
    'UPDATE_COORDS_GUIDE.md',
    'LICENSE',  # 如果有许可证文件
}

# 要删除的文件
FILES_TO_DELETE = [
    'COORDINATE_SYSTEM_FIX.md',
    'CSV_IMPORT_GUIDE.md',
    'DATA_GUIDE.md',
    'FEATURES_GUIDE.md',
    'FILTER_AND_FAVORITES_GUIDE.md',
    'FINAL_COORDINATE_FIX.md',
    'FIX_LOCATION_DISPLAY.md',
    'FIX_ROUTE_AND_MAP.md',
    'LOCATION_AND_MAP_CONTROLS_GUIDE.md',
    'LOCATION_FIX_GUIDE.md',
    'MAP_COORDINATE_FIX.md',
    'NAVIGATION_BUTTONS_GUIDE.md',
    'OPTIMIZATION_NOTES.md',
    'QUICK_START.md',
    'SEARCH_FEATURE_GUIDE.md',
    'SEARCH_FIX.md',
    'SEARCH_TROUBLESHOOTING.md',
    'SETTINGS_BUTTON_FIX.md',
]

def cleanup_docs():
    """清理文档文件"""
    print("=" * 60)
    print("📝 开始清理过时文档")
    print("=" * 60)
    
    deleted_count = 0
    skipped_count = 0
    
    for filename in FILES_TO_DELETE:
        filepath = PROJECT_ROOT / filename
        
        if filepath.exists():
            try:
                filepath.unlink()
                print(f"✅ 已删除: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ 删除失败 {filename}: {e}")
        else:
            print(f"⏭️  跳过(不存在): {filename}")
            skipped_count += 1
    
    print("\n" + "=" * 60)
    print("📊 清理完成统计:")
    print(f"   删除: {deleted_count} 个文件")
    print(f"   跳过: {skipped_count} 个文件")
    print("=" * 60)
    
    # 显示保留的文件
    print("\n✅ 保留的核心文档:")
    for filename in KEEP_FILES:
        filepath = PROJECT_ROOT / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"   📄 {filename} ({size/1024:.1f} KB)")
    
    print("\n💡 提示:")
    print("   - README.md: 项目简介和快速开始")
    print("   - DEVELOPER_GUIDE.md: 技术架构和API文档")
    print("   - PPT_PRESENTATION_OUTLINE.md: 汇报材料")
    print("   - UPDATE_COORDS_GUIDE.md: 坐标更新工具说明")

if __name__ == '__main__':
    confirm = input("⚠️  此操作将永久删除18个过时文档,是否继续? (yes/no): ")
    if confirm.lower() == 'yes':
        cleanup_docs()
    else:
        print("已取消操作")


