#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <unordered_set>
#include <filesystem>
#include <algorithm>
// #include <nlohmann/json.hpp>
#include "json.hpp"
#include <locale>


using json = nlohmann::json;
using namespace std;
namespace fs = std::filesystem;

void extractWords(const std::string &text, std::unordered_set<std::string> &lex) {
    std::string w;

    auto processWord = [&lex](std::string &word) {
        if (!word.empty()) {
            lex.insert(word);
            word.clear();
        }
    };

    for (unsigned char c : text) {
        if (std::isalnum(c) || c >= 128) {
            if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z'))
                w.push_back(std::tolower(c));
            else
                w.push_back(c);  // numbers and non-ASCII
        } else {
            processWord(w);
        }
    }

    processWord(w);
}

void parseJsonFile(const fs::path &path, unordered_set<string> &lex) {
    ifstream in(path);
    if (!in) {
        cerr << "[WARN] Cannot open file: " << path << endl;
        return;
    }

    json j;
    try {
        in >> j;
    } catch (const std::exception &e) {
        cerr << "[WARN] Invalid JSON in file: " << path 
             << " (" << e.what() << ")" << endl;
        return;
    }

    // --- title ---
    if (j.contains("metadata") && j["metadata"].contains("title"))
        extractWords(j["metadata"]["title"].get<string>(), lex);

    // --- authors ---
    if (j.contains("metadata") && j["metadata"].contains("authors")) {
        for (auto &author : j["metadata"]["authors"]) {
            if (author.is_string()){
                extractWords(author.get<string>(), lex);
                continue;
            }
            // On all attributes of author object
            for (auto &[key, value] : author.items()) {
                if (value.is_string())
                    extractWords(value.get<string>(), lex);
            }
        }
    }

    // --- abstract ---
    if (j.contains("abstract")) {
        for (auto &obj : j["abstract"]) {
            if (obj.contains("text"))
                extractWords(obj["text"].get<string>(), lex);
        }
    }

    // --- body_text ---
    if (j.contains("body_text")) {
        for (auto &obj : j["body_text"]) {
            if (obj.contains("text"))
                extractWords(obj["text"].get<string>(), lex);
        }
    }

    // --- bib_entries titles ---
    if (j.contains("bib_entries")) {
        for (auto &[key, entry] : j["bib_entries"].items()) {
            if (entry.contains("title"))
                extractWords(entry["title"].get<string>(), lex);
        }
    }

    // --- ref_entries (figures, tables, extra sections) ---
    if (j.contains("ref_entries")) {
        for (auto &[key, entry] : j["ref_entries"].items()) {
            if (entry.contains("text"))
                extractWords(entry["text"].get<string>(), lex);
        }
    }

    // --- back_matter ---
    if (j.contains("back_matter")) {
        for (auto &obj : j["back_matter"]) {
            if (obj.contains("text"))
                extractWords(obj["text"].get<string>(), lex);
        }
    }
}

// -----------------------------------------------------------
// Build lexicon by scanning folder
// -----------------------------------------------------------
unordered_set<string> buildLexicon(const fs::path &folder) {
    unordered_set<string> lex;
    if (!fs::exists(folder)) {
        cerr << "[ERROR] Folder does not exist: " << folder << endl;
        return lex;
    }

    int count = 0;
    for (auto &entry : fs::directory_iterator(folder)) {
        if (entry.is_regular_file() && entry.path().extension() == ".json") {
            parseJsonFile(entry.path(), lex);
            count++;
            if (count % 50 == 0)
                cout << count << " files processed..." << endl;
        }
    }

    cout << "Processed total files: " << count << endl;
    return lex;
}

// -----------------------------------------------------------
// Write words to text file (1 per line, sorted)
// -----------------------------------------------------------
void writeWords(const unordered_set<string> &lex, const fs::path &out) {
    vector<string> words(lex.begin(), lex.end());
    sort(words.begin(), words.end());

    ofstream f(out);
    if (!f) {
        cerr << "[ERROR] Cannot write to file: " << out << endl;
        return;
    }

    for (const string &w : words)
        f << w << "\n";
}

// -----------------------------------------------------------
// MAIN
// -----------------------------------------------------------
int main() {
    fs::path folder_path = "..\\Data\\Cord 19\\document_parses\\pdf_json";
    
    fs::path folder(folder_path);

    unordered_set<string> lex = buildLexicon(folder);

    if (lex.empty()) {
        cout << "No words extracted. Exiting." << endl;
        return 0;
    }

    fs::path output = "..\\Lexicon\\words.txt";
    writeWords(lex, output);

    cout << "Done. Total unique words: " << lex.size() << endl;
    cout << "Saved to: " << output << endl;

    return 0;
}