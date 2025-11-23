#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <unordered_set>
#include <filesystem>
#include <algorithm>
#include <nlohmann/json.hpp>

using json = nlohmann::json;
using namespace std;
namespace fs = std::filesystem;

// -----------------------------------------------------------
// Split arbitrary text into lowercase words
// -----------------------------------------------------------
void extractWords(const string &text, unordered_set<string> &lex) {
    string w;
    for (char c : text) {
        if (isalpha(c)) {
            w.push_back(tolower(c));
        } else {
            if (!w.empty()) {
                // FILTER STEP
                bool keep = true;

                // Skip very long words (>20 chars)
                if (w.length() > 20) keep = false;

                // Skip words mostly repeated letters (>80% same)
                if (keep) {
                    int max_count = 0;
                    for (char ch = 'a'; ch <= 'z'; ++ch) {
                        int count = count_if(w.begin(), w.end(), [ch](char c){ return c == ch; });
                        if (count > max_count) max_count = count;
                    }
                    if ((double)max_count / w.size() > 0.8)
                        keep = false;
                }

                // Skip words with very unusual patterns (optional)
                if (keep && w.find('u') != string::npos) {
                    // treat 'u' in long words as RNA sequence indicator
                    if (w.length() > 5) keep = false;
                }

                if (keep)
                    lex.insert(w);

                w.clear();
            }
        }
    }

    // Check last word
    if (!w.empty()) {
        bool keep = true;
        if (w.length() > 20) keep = false;

        int max_count = 0;
        for (char ch = 'a'; ch <= 'z'; ++ch) {
            int count = count_if(w.begin(), w.end(), [ch](char c){ return c == ch; });
            if (count > max_count) max_count = count;
        }
        if ((double)max_count / w.size() > 0.8) keep = false;
        if (keep) lex.insert(w);
    }
}

// -----------------------------------------------------------
// Parse a single JSON file safely
// -----------------------------------------------------------
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
        cerr << "[WARN] Invalid JSON in file: " << path << " (" << e.what() << ")" << endl;
        return;
    }

    // --- title ---
    if (j.contains("metadata") && j["metadata"].contains("title"))
        extractWords(j["metadata"]["title"].get<string>(), lex);

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
    fs::path folder_path = "Data\\cord-19_2020-05-12\\2020-05-12\\document_parses\\pdf_json";
    
    fs::path folder(folder_path);

    unordered_set<string> lex = buildLexicon(folder);

    if (lex.empty()) {
        cout << "No words extracted. Exiting." << endl;
        return 0;
    }

    fs::path output = "Data\\Lexicon\\words.txt";
    writeWords(lex, output);

    cout << "Done. Total unique words: " << lex.size() << endl;
    cout << "Saved to: " << output << endl;

    return 0;
}