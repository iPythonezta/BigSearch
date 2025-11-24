def main():
    json_files_lexicon = "..\\Lexicon\\words.txt"
    html_files_lexicon = "..\\Lexicon\\final_lexicon.txt"

    final = set()


    with open(json_files_lexicon, 'r', encoding='utf-8') as f:
        json = f.readlines()
    
    with open(html_files_lexicon, 'r', encoding='utf-8') as f:
        html = f.readlines()

    final.update(json)
    final.update(html)

    with open("..\\Lexicon\\final_words_lexicon.txt", 'w', encoding='utf-8') as f:
        sorted_final = sorted(final)
        f.writelines(sorted_final)

if __name__ == "__main__":
    main()