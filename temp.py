from pathlib import Path
import os
import sys


class DirectoryTree:
    def __init__(self, root_path, show_files=True, max_depth=None, show_hidden=False):
        self.root_path = Path(root_path)
        self.show_files = show_files
        self.max_depth = max_depth
        self.show_hidden = show_hidden
        self.total_dirs = 0
        self.total_files = 0

    def generate_tree(self):
        """Генерирует и отображает дерево каталогов"""
        if not self.root_path.exists():
            print(f"Ошибка: путь '{self.root_path}' не существует")
            return

        print(f"\n📁 Дерево каталогов: {self.root_path.absolute()}")
        print("=" * 60)

        self._walk_directory(self.root_path, "", 0)

        print("=" * 60)
        print(f"📊 Итого: {self.total_dirs} директорий, {self.total_files} файлов")

    def _walk_directory(self, path, prefix, depth):
        """Рекурсивный обход директорий"""
        if self.max_depth and depth > self.max_depth:
            return

        # Получаем содержимое директории
        try:
            items = sorted([item for item in path.iterdir()], key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            print(f"{prefix}└── [Доступ запрещен]")
            return

        # Фильтруем скрытые файлы
        if not self.show_hidden:
            items = [item for item in items if not item.name.startswith('.')]

        # Обрабатываем каждый элемент
        for index, item in enumerate(items):
            is_last = (index == len(items) - 1)

            # Определяем символы для отображения
            connector = "└── " if is_last else "├── "

            if item.is_dir():
                self.total_dirs += 1
                print(f"{prefix}{connector}📁 {item.name}/")

                # Рекурсивный вызов для поддиректорий
                extension = "    " if is_last else "│   "
                self._walk_directory(item, prefix + extension, depth + 1)
            elif self.show_files:
                self.total_files += 1
                # Получаем размер файла
                size = self._get_file_size(item)
                # Определяем иконку по расширению
                icon = self._get_file_icon(item)
                print(f"{prefix}{connector}{icon} {item.name} ({size})")

    def _get_file_size(self, file_path):
        """Возвращает размер файла в читаемом формате"""
        try:
            size = file_path.stat().st_size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            elif size < 1024 * 1024 * 1024:
                return f"{size / (1024 * 1024):.1f} MB"
            else:
                return f"{size / (1024 * 1024 * 1024):.1f} GB"
        except:
            return "?? B"

    def _get_file_icon(self, file_path):
        """Возвращает иконку в зависимости от типа файла"""
        suffixes = {
            '.py': '🐍', '.js': '📜', '.html': '🌐', '.css': '🎨',
            '.json': '📋', '.xml': '📄', '.csv': '📊', '.txt': '📝',
            '.md': '📖', '.pdf': '📕', '.doc': '📘', '.xls': '📗',
            '.jpg': '🖼️', '.png': '🖼️', '.gif': '🎬', '.mp4': '🎥',
            '.mp3': '🎵', '.zip': '📦', '.exe': '⚙️'
        }

        for suffix, icon in suffixes.items():
            if file_path.suffix.lower() == suffix:
                return icon

        return '📄'


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Отображение структуры файлов и каталогов')
    parser.add_argument('path', nargs='?', default='.', help='Путь к директории (по умолчанию: текущая)')
    parser.add_argument('-f', '--files', action='store_true', help='Показывать файлы')
    parser.add_argument('-d', '--depth', type=int, help='Максимальная глубина рекурсии')
    parser.add_argument('-a', '--all', action='store_true', help='Показывать скрытые файлы')

    args = parser.parse_args()

    tree = DirectoryTree(
        root_path=args.path,
        show_files=True,  # Файлы будут показываться по умолчанию
        max_depth=args.depth,
        show_hidden=args.all
    )

    tree.generate_tree()


if __name__ == "__main__":
    main()