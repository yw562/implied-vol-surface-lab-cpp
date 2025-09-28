#include "quant_utils.hpp"
#include <iostream>
#include <iomanip>

int main(int argc, char** argv){
    using namespace qx;
    using std::cout; using std::cerr;

    if(argc < 6){
        cerr << "Usage:\n"
             << "  iv_lab <csv_path> <S> <T_years> <r_rate> <type>\n"
             << "Example:\n"
             << "  iv_lab data/sample_quotes.csv 100 0.5 0.02 put\n";
        return 1;
    }

    std::string csv = argv[1];
    double S = std::stod(argv[2]);
    double T = std::stod(argv[3]);
    double r = std::stod(argv[4]);
    std::string typ = argv[5];

    // 读入报价
    auto quotes = read_quotes_csv(csv);
    if(quotes.empty()){ cerr << "No quotes read.\n"; return 1; }

    // 价格→IV
    std::vector<double> K, px, iv;
    for(const auto& q: quotes){
        double iv_i = implied_vol(q.price, S, q.K, T, r, q.is_call);
        K.push_back(q.K); px.push_back(q.price); iv.push_back(iv_i);
    }
    write_csv("out/iv_observed.csv", K, iv, "IV");
    cout << "[OK] Wrote out/iv_observed.csv\n";

    // 过滤：moneyness 与 IV 合理区间
    std::vector<double> Kf, ivf;
    for(size_t i=0;i<K.size();++i){
        double m = K[i]/S;
        if(m>0.7 && m<1.3 && std::isfinite(iv[i]) && iv[i]>0.01 && iv[i]<3.0){
            Kf.push_back(K[i]); ivf.push_back(iv[i]);
        }
    }
    if(Kf.size() < 8){ cerr << "Too few clean points for poly fit.\n"; return 0; }

    // 三次多项式拟合
    auto coef = fit_cubic_poly(Kf, ivf, S);
    auto iv_fit = eval_cubic_poly(K, coef, S);
    write_csv("out/iv_poly_fit.csv", K, iv_fit, "IV_poly");
    cout << "[OK] Wrote out/iv_poly_fit.csv\n";

    // 示例：打印 ATM put 的 Greeks
    double test_sigma = 0.2;
    double test_price = bs_put(S, S, T, r, test_sigma);
    double sigma_atm = implied_vol(test_price, S, S, T, r, false);
    if(std::isfinite(sigma_atm) && sigma_atm>0){
        auto g_put = greeks_put(S,S,T,r,sigma_atm);
        cout << std::fixed << std::setprecision(6)
             << "ATM put Greeks (iv≈" << sigma_atm << "): "
             << "Delta=" << g_put.delta << " Gamma=" << g_put.gamma
             << " Vega=" << g_put.vega  << " Theta=" << g_put.theta
             << " Rho=" << g_put.rho   << "\n";
    }

    cout << "[DONE] Price->IV inversion + cubic polynomial smile fit completed.\n";
    return 0;
}
