
#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <vector>
#include <map>

using namespace std;

int main(int argc, char* argv[]) {
    // open csv file
    ifstream file("data/prices.csv");

    if (!file.is_open()) {
        cout << "Error: Could not open file!" << endl;
        return 1;
    }

    string line;
    double threshold{100.0};
    string startDate{};
    string endDate{};

    // if user changes threshold, update it
    if (argc > 1) {
        threshold = stod(argv[1]);
    }

    // get start and end dates from python
    if (argc > 2) {
        startDate = argv[2];
    }

    if (argc > 3) {
        endDate = argv[3];
    }

    // skip header (Date, hour, price)
    getline(file, line);

    // vectors to store data from csv
    vector<string> dates;
    vector<int> hours;
    vector<double> prices;

    // read each row of csv
    while (getline(file, line)) {

        // create obj to read from line
        stringstream ss(line);

        string date;
        string hour;
        string price;

        // separate each column using commas
        getline(ss, date, ',');
        getline(ss, hour, ',');
        getline(ss, price, ',');

        // skip dates outside selected range
        if (startDate != "" && date < startDate) {
            continue;
        }

        if (endDate != "" && date > endDate) {
            continue;
        }

        // convert strings to int and double
        int hourValue = stoi(hour);
        double priceValue = stod(price);

        // append into vector
        dates.push_back(date);
        hours.push_back(hourValue);
        prices.push_back(priceValue);

        cout << "Date: " << date
        << " | Hour: " << hourValue
        << " | Price: $" << priceValue
        << endl;
    }

    double total{0};

    // calc the total of all prices from prices vector
    for (double price : prices) {
        total += price;
    }

    // calculate the avg, min, max
    if (!prices.empty()) {
        double average = total / prices.size();
        double minPrice = prices[0];
        double maxPrice = prices[0];

        // go through prices to find lowest and highest
        for (double currentPrice : prices) {
            if (currentPrice < minPrice) {
                minPrice = currentPrice;
            }

            if (currentPrice > maxPrice) {
                maxPrice = currentPrice;
            }
        }

        cout << "Average price: $" << average << "\n";
        cout << "Minimum price: $" << minPrice << "\n";
        cout << "Maximum price: $" << maxPrice << endl;
    }

    cout << "Current threshold: $" << threshold << endl;

    int spikes{0};

    // create csv to store detected price spikes
    ofstream spikeOutput("data/spikes.csv");

    if (!spikeOutput.is_open()) {
        cout << "Error creating spikes.csv!" << endl;
        return 1;
    }

    // write csv header
    spikeOutput << "Date,Hour,Price" << endl;

    // detect when spikes
    for (size_t i = 0; i < prices.size(); i++) {
        if (prices[i] > threshold) {
            spikes++;

            cout << "Price spike detected!" << "\n";
            cout << "Date: " << dates[i] << "\n";
            cout << "Hour: " << hours[i] << "\n";
            cout << "Price: $" << prices[i] << endl;

            // save spike info to csv
            spikeOutput << dates[i] << ','
            << hours[i] << ','
            << prices[i] << endl;
        }
    }

    spikeOutput.close();

    cout << "Total spikes: " << spikes << endl;

    // calc spike percentage
    if (!prices.empty()) {
        double spikePercent = static_cast<double>(spikes) / prices.size() * 100;

        cout << "Spike percentage: " << spikePercent << '%' << endl;
    }

    // vectors to store total prices and counts for each hour
    vector<double> hourlyTotal(24, 0.0);
    vector<int> hourlyCounts(24, 0);

    // go through each price and group it by hour
    for (size_t i = 0; i < prices.size(); i++) {
        int hour = hours[i];

        if (hour >= 0 && hour < 24) {

            // add all prices to certain hour
            hourlyTotal[hour] += prices[i];

            // add how many times an hour shows up
            hourlyCounts[hour]++;
        }
    }

    // create csv for hourly averages
    ofstream output("data/hourly_averages.csv");

    if (!output.is_open()) {
        cout << "Error: Could not create output file!" << endl;
        return 1;
    }

    output << "Hour,AveragePrice" << endl;

    // calculate avg prices for hours
    for (int hour = 0; hour < 24; hour++) {
        if (hourlyCounts[hour] > 0) {
            double hourlyAvg = hourlyTotal[hour] / hourlyCounts[hour];

            cout << "Hour " << hour
            << ": Average price = $" << hourlyAvg
            << endl;

            // write hour and avg price to csv
            output << hour << ',' << hourlyAvg << endl;
        }
    }

    output.close();

    cout << "Hourly averages exported succesfully!" << endl;

    // maps to store total prices and counts for each date
    map<string, double> dailyTotals;
    map<string, int> dailyCounts;

    // group prices by date
    for (size_t i = 0; i < prices.size(); i++) {
        string date = dates[i];

        // add prices for the same date
        dailyTotals[date] += prices[i];

        // count how many prices are on each date
        dailyCounts[date]++;
    }

    // create csv for daily averages
    ofstream dailyOutput("data/daily_averages.csv");

    if (!dailyOutput.is_open()) {
        cerr << "Error creating daily_averages.csv" << endl;
        return 1;
    }

    dailyOutput << "Date,AveragePrice\n";

    // calculate avg for each date
    for (const auto& entry : dailyTotals) {
        string date = entry.first;
        double total = entry.second;

        double dailyAvg = total / dailyCounts[date];

        // save daily avg to csv
        dailyOutput << date << ',' << dailyAvg << '\n';
    }

    dailyOutput.close();

    cout << "Daily averages exported sucessfully!" << endl;

    file.close();

    // calculate overall stats and save to summary csv
    if (!prices.empty()) {
        double avg = total / prices.size();
        double minPrice = prices[0];
        double maxPrice = prices[0];

        // find min and max prices
        for (double currentPrice : prices) {
            if (currentPrice < minPrice) {
                minPrice = currentPrice;
            }

            if (currentPrice > maxPrice) {
                maxPrice = currentPrice;
            }
        }

        // create summary csv
        ofstream stats("data/summary.csv");

        if (!stats.is_open()) {
            cerr << "Error creating summary.csv" << endl;
            return 1;
        }

        // write avg, min and max into csv
        stats << "Average,Minimum,Maximum\n";
        stats << avg << ',' << minPrice << ',' << maxPrice << "\n";

        stats.close();
    }

    return 0;
}
