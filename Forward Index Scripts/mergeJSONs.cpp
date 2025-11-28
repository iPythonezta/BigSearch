#include <iostream>
#include <fstream>
#include <string>
#include <map>
#include <vector>
#include <filesystem>
#include <nlohmann/json.hpp>

namespace fs = std::filesystem;
using json = nlohmann::json;

int main() {
    std::string folderPath = R"(C:\Users\windows10\Lexicon\BigSearch\Forward Index)";

    // Use sorted map to collect all docIDs -> word lists
    std::map<int, std::vector<int>> sortedMap;

    for (auto &entry : fs::directory_iterator(folderPath)) {
        if (entry.path().extension() == ".json" &&
            entry.path().filename().string().find("forward_index_batch") != std::string::npos)
        {
            std::ifstream in(entry.path());
            if (!in.is_open()) continue;

            json batch;
            in >> batch;
            in.close();

            // Merge batch into sorted map
            for (auto &item : batch.items()) {
                int docId = std::stoi(item.key());
                sortedMap[docId] = item.value().get<std::vector<int>>();
            }

            batch.clear();
            json().swap(batch); // free memory
        }
    }

    // Convert map into a JSON array (order guaranteed)
    json arrayJson = json::array();
    for (auto &[docId, words] : sortedMap) {
        json entry;
        entry["doc_id"] = docId;
        entry["words"] = words;
        arrayJson.push_back(entry);
    }

    // Convert JSON array back into JSON object, preserving order
    json finalJson = json::object();
    for (auto &item : arrayJson) {
        finalJson[std::to_string(item["doc_id"].get<int>())] = item["words"];
    }

    // Save final JSON object
    std::string outPath = folderPath + "\\forward_index_json.json";
    std::ofstream out(outPath);
    out << finalJson.dump(2);
    out.close();

    std::cout << "[DONE] Final sorted JSON object written to: " << outPath << std::endl;

    return 0;
}
