#include <iostream>
#include <vector>
#include <fstream>
#include <sstream>
#include <filesystem>
#include <algorithm>
#include <cmath>

using namespace std;

vector<vector<int>> loadLinkDataFile(string& file_path){
    ifstream file(file_path);
    vector<vector<int>> adjList (102354); 
    
    if (!file.is_open()){
        cout << "Couldn't open the file" << endl;
        return adjList;
    }
    

    int from_link, to_link;
    char comma;
    string line;
    getline(file, line); // Skip header line
    while (getline(file, line)){
        stringstream ss(line);
        ss >> from_link >> comma >> to_link;
        adjList[from_link].push_back(to_link);
    }
    file.close();
    return adjList;
}

vector<double> calculatePageRank(const vector<vector<int>>& adjList, double converge_limit, double d = 0.85) {
    int n = adjList.size();
    vector<double> pageRank(n, 1.0 / n);
    vector<double> newPageRank(n, 0.0);
    double dangling_sum;
    double page_rank_sum = 0;
    int it = 0;
    double diff = 1.0;
    while (diff > converge_limit) {
        it++;
        dangling_sum = 0.0;
        fill(newPageRank.begin(), newPageRank.end(), 0.0);

        for (int i = 0; i < n; i++) {
            int outDegree = adjList[i].size();
            if (outDegree == 0){
                dangling_sum += pageRank[i];
                continue;
            }
            double share = pageRank[i] / outDegree;
            for (int neighbor : adjList[i]) {
                newPageRank[neighbor] += share;
            }
        }

        for (int i = 0; i < n; ++i) {
            newPageRank[i] = (1 - d) / n + d * (newPageRank[i] + dangling_sum / n);
        }

        diff = 0.0;
        for (int i = 0; i < n; ++i) {
            diff += fabs(newPageRank[i] - pageRank[i]);
        }

        cout << "Iteration " << it << ", diff = " << diff << endl;
        swap(pageRank, newPageRank);
    }
    return pageRank;
}


void writePageRankToFile(const vector<double>& pageRank, const string& file_path) {
    ofstream file(file_path);
    vector<pair<int, double>> rankWithId;
    for (int i = 0; i < pageRank.size(); i++) {
        rankWithId.emplace_back(i, pageRank[i]);
    }
    sort(rankWithId.begin(), rankWithId.end(), [](const pair<int, double>& a, const pair<int, double>& b) {
        return b.second < a.second;
    });
    for (const auto& p : rankWithId) {
        file << p.first << "," << p.second << "\n";
    }
    file.close();
    return;
}

int main() {
    namespace fs = std::filesystem;
    auto cwd = fs::current_path();
    auto page_rank_link_path = cwd / "Data" / "Page_rank_files" / "page_rank_links_ids.csv";
    auto domain_rank_link_path = cwd / "Data" / "Page_rank_files" / "domain_rank_links_ids.csv";
    auto output_path = cwd / "Page Rank Results" / "page_rank_output.csv";
    auto domain_output_path = cwd / "Page Rank Results" / "domain_rank_output.csv";


    // string file_path_pages = page_rank_link_path.string();
    // vector<vector<int>> adjList = loadLinkDataFile(file_path_pages);
    // cout << "Loaded adjacency list with " << adjList.size() << " nodes." << endl;

    // vector<double> pageRank = calculatePageRank(adjList, 1e-8);
    // writePageRankToFile(pageRank, output_path.string());
    // cout << "PageRank calculation completed and written to " << output_path.string() << endl;

    string file_path_domains = domain_rank_link_path.string();
    vector<vector<int>> adjListDomains = loadLinkDataFile(file_path_domains);
    
    cout << "Loaded domain adjacency list with " << adjListDomains.size() << " nodes." << endl;
    vector<double> domainPageRank = calculatePageRank(adjListDomains, 1e-8);
    writePageRankToFile(domainPageRank, domain_output_path.string());
    cout << "Domain PageRank calculation completed and written to " << domain_output_path.string() << endl;

    return 0;
}