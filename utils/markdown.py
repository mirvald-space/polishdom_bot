def escape_markdown(text: str) -> str:
    """Escape special characters for MarkdownV2 while preserving intended Markdown formatting."""
    # Сначала заменяем все экранированные звездочки на временный маркер
    text = text.replace('\\*', '§STAR§')
    
    # Заменяем спойлеры на временный маркер
    text = text.replace('||', '‖')
    
    # Экранируем специальные символы
    special_chars = ['_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    # Восстанавливаем экранированные звездочки и добавляем экранирование для одиночных звездочек
    text = text.replace('§STAR§', '\\*')
    
    # Заменяем парные звездочки на экранированные
    text = text.replace('**', '*')
    
    # Восстанавливаем спойлеры
    text = text.replace('‖', '||')
    
    return text 