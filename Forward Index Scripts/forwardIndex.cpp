#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <filesystem>
#include <algorithm>
#include <nlohmann/json.hpp>
// #include "json.hpp"

using namespace std;
using json = nlohmann::json;
namespace fs = std::filesystem;

// ----------------- Reuse of extractWords -----------------
void extractWords(const string &text, unordered_set<string> &wordsSet) {
    string word;
    auto processWord = [&wordsSet](string &w) {
        if (!w.empty()) {
            wordsSet.insert(w);
            w.clear();
        }
    };

    for (unsigned char c : text) {
        if (isalnum(c) || c >= 128) {
            word.push_back(tolower(c));
        } else {
            processWord(word);
        }
    }
    processWord(word);
}

// ----------------- Parse JSON file per document -----------------
unordered_set<string> parseJsonFile(const fs::path &path) {
    unordered_set<string> words;
    ifstream in(path);
    if (!in) {
        cerr << "[WARN] Cannot open file: " << path << endl;
        return words;
    }

    json j;
    try {
        in >> j;
    } catch (const exception &e) {
        cerr << "[WARN] Invalid JSON in file: " << path << " (" << e.what() << ")" << endl;
        return words;
    }

    // --- reuse of previous sections ---
    if (j.contains("metadata") && j["metadata"].contains("title"))
        extractWords(j["metadata"]["title"].get<string>(), words);

    if (j.contains("metadata") && j["metadata"].contains("authors")) {
        for (auto &author : j["metadata"]["authors"]) {
            if (author.is_string()) {
                extractWords(author.get<string>(), words);
                continue;
            }
            for (auto &[key, value] : author.items()) {
                if (value.is_string())
                    extractWords(value.get<string>(), words);
            }
        }
    }

    if (j.contains("abstract")) {
        for (auto &obj : j["abstract"]) {
            if (obj.contains("text"))
                extractWords(obj["text"].get<string>(), words);
        }
    }

    if (j.contains("body_text")) {
        for (auto &obj : j["body_text"]) {
            if (obj.contains("text"))
                extractWords(obj["text"].get<string>(), words);
        }
    }

    if (j.contains("bib_entries")) {
        for (auto &[key, entry] : j["bib_entries"].items()) {
            if (entry.contains("title"))
                extractWords(entry["title"].get<string>(), words);
        }
    }

    if (j.contains("ref_entries")) {
        for (auto &[key, entry] : j["ref_entries"].items()) {
            if (entry.contains("text"))
                extractWords(entry["text"].get<string>(), words);
        }
    }

    if (j.contains("back_matter")) {
        for (auto &obj : j["back_matter"]) {
            if (obj.contains("text"))
                extractWords(obj["text"].get<string>(), words);
        }
    }

    return words;
}

// ----------------- Load Lexicon -----------------
unordered_map<string, int> loadLexicon(const fs::path &lexiconPath) {
    unordered_map<string, int> lexiconMap;
    ifstream lexFile(lexiconPath);
    if (!lexFile) {
        cerr << "[ERROR] Cannot open lexicon file: " << lexiconPath << endl;
        return lexiconMap;
    }

    json lexJson;
    lexFile >> lexJson;
    for (auto &[word, id] : lexJson.items())
        lexiconMap[word] = id.get<int>();

    return lexiconMap;
}

// ----------------- Build Forward Index -----------------
unordered_map<string, vector<int>> buildForwardIndexFromFolder(
    const fs::path &folder,
    const unordered_map<string, int> &lexiconMap
) {
    unordered_map<string, vector<int>> forwardIndex;
    int count = 0;

    for (auto &entry : fs::directory_iterator(folder)) {
        if (entry.is_regular_file() && entry.path().extension() == ".json") {
            string docId = entry.path().stem().string();
            unordered_set<string> words = parseJsonFile(entry.path());

            vector<int> wordIds;
            for (const string &w : words) {
                if (lexiconMap.count(w))
                    wordIds.push_back(lexiconMap.at(w));
            }

            forwardIndex[docId] = wordIds;
            count++;

            if (count % 100 == 0) // print every 100 files
                cout << "[INFO] Processed " << count << " files. Last doc: " << docId << endl;
        }
    }

    cout << "[INFO] Finished processing " << count << " files." << endl;
    return forwardIndex;
}


// ----------------- Save Forward Index -----------------
void saveForwardIndexToFile(
    const unordered_map<string, vector<int>> &forwardIndex,
    const fs::path &outPath
) {
    json j;
    for (auto &[docId, wordIds] : forwardIndex)
        j[docId] = wordIds;

    ofstream f(outPath);
    if (!f) {
        cerr << "[ERROR] Cannot write file: " << outPath << endl;
        return;
    }
    f << setw(2) << j << endl;
}

// ----------------- MAIN -----------------
int main() {
    fs::path folderPath = "../Data/Cord 19/document_parses/pdf_json";
    fs::path lexiconPath = "../Lexicon/lexicons_ids.json";
    fs::path outputPath = "../Forward Index/forward_index_json_files.json";

    // Load lexicon
    auto lexiconMap = loadLexicon(lexiconPath);
    if (lexiconMap.empty()) return 1;

    // Build forward index
    auto forwardIndex = buildForwardIndexFromFolder(folderPath, lexiconMap);

    // Save forward index
    saveForwardIndexToFile(forwardIndex, outputPath);

    cout << "Forward index built. Total documents: " << forwardIndex.size() << endl;
    return 0;
}
