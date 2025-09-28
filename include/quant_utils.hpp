#pragma once
#include <cmath>
#include <vector>
#include <string>
#include <limits>
#include <stdexcept>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <cctype>

namespace qx {

// -------- Normal CDF / PDF --------
inline double norm_pdf(double x){
    static constexpr double INV_SQRT_2PI = 0.3989422804014327;
    return INV_SQRT_2PI * std::exp(-0.5 * x * x);
}
inline double norm_cdf(double x){
    // Abramowitz–Stegun approximation
    static constexpr double a1=0.254829592, a2=-0.284496736, a3=1.421413741;
    static constexpr double a4=-1.453152027, a5=1.061405429, p=0.3275911;
    int sign = (x < 0) ? -1 : 1;
    x = std::fabs(x) / std::sqrt(2.0);
    double t = 1.0 / (1.0 + p*x);
    double y = 1.0 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1)*t*std::exp(-x*x);
    return 0.5 * (1.0 + sign * y);
}

// -------- Black–Scholes --------
inline double d1(double S,double K,double T,double r,double sigma){
    return (std::log(S/K) + (r + 0.5*sigma*sigma)*T) / (sigma*std::sqrt(T));
}
inline double d2(double S,double K,double T,double r,double sigma){
    return d1(S,K,T,r,sigma) - sigma*std::sqrt(T);
}
inline double bs_call(double S,double K,double T,double r,double sigma){
    if(sigma<=0 || T<=0) return std::max(0.0, S - K*std::exp(-r*T));
    double D1=d1(S,K,T,r,sigma), D2=d2(S,K,T,r,sigma);
    return S*norm_cdf(D1) - K*std::exp(-r*T)*norm_cdf(D2);
}
inline double bs_put(double S,double K,double T,double r,double sigma){
    if(sigma<=0 || T<=0) return std::max(0.0, K*std::exp(-r*T) - S);
    double D1=d1(S,K,T,r,sigma), D2=d2(S,K,T,r,sigma);
    return K*std::exp(-r*T)*norm_cdf(-D2) - S*norm_cdf(-D1);
}

// Greeks
struct Greeks { double delta, gamma, vega, theta, rho; };
inline Greeks greeks_call(double S,double K,double T,double r,double sigma){
    double D1=d1(S,K,T,r,sigma), D2=d2(S,K,T,r,sigma);
    double pdf = norm_pdf(D1);
    Greeks g;
    g.delta = norm_cdf(D1);
    g.gamma = pdf / (S * sigma * std::sqrt(T));
    g.vega  = S * pdf * std::sqrt(T);
    g.theta = - (S*pdf*sigma)/(2*std::sqrt(T)) - r*K*std::exp(-r*T)*norm_cdf(D2);
    g.rho   = K*T*std::exp(-r*T)*norm_cdf(D2);
    return g;
}
inline Greeks greeks_put(double S,double K,double T,double r,double sigma){
    double D1=d1(S,K,T,r,sigma), D2=d2(S,K,T,r,sigma);
    double pdf = norm_pdf(D1);
    Greeks g;
    g.delta = norm_cdf(D1) - 1.0;
    g.gamma = pdf / (S * sigma * std::sqrt(T));
    g.vega  = S * pdf * std::sqrt(T);
    g.theta = - (S*pdf*sigma)/(2*std::sqrt(T)) + r*K*std::exp(-r*T)*norm_cdf(-D2);
    g.rho   = -K*T*std::exp(-r*T)*norm_cdf(-D2);
    return g;
}

// -------- Brent root finder（price->IV） --------
inline double implied_vol(double price,double S,double K,double T,double r,bool is_call,
                          double lo=1e-6,double hi=5.0, int maxit=200, double xtol=1e-10){
    auto f = [&](double sig){
        return is_call ? (bs_call(S,K,T,r,sig)-price) : (bs_put(S,K,T,r,sig)-price);
    };
    double flo=f(lo), fhi=f(hi);
    if(std::isnan(flo) || std::isnan(fhi) || flo*fhi>0.0) return std::numeric_limits<double>::quiet_NaN();

    double a=lo, b=hi, fa=flo, fb=fhi, c=a, fc=fa, d=c;
    bool mflag=true; double s=b; double fs=fb;

    for(int iter=0; iter<maxit; ++iter){
        if(fa!=fc && fb!=fc){
            s = ( a*fb*fc / ((fa-fb)*(fa-fc)) )
              + ( b*fa*fc / ((fb-fa)*(fb-fc)) )
              + ( c*fa*fb / ((fc-fa)*(fc-fb)) );
        } else {
            s = b - fb*(b-a)/(fb-fa);
        }
        bool cond1 = (s < (3*a+b)/4 || s > b);
        bool cond2 = (mflag && std::fabs(s-b) >= std::fabs(b-c)/2);
        bool cond3 = (!mflag && std::fabs(s-b) >= std::fabs(c-d)/2);
        bool cond4 = (mflag && std::fabs(b-c) < xtol);
        bool cond5 = (!mflag && std::fabs(c-d) < xtol);

        d=c;
        if(cond1 || cond2 || cond3 || cond4 || cond5){ s = 0.5*(a+b); mflag = true; }
        else                                          { mflag = false; }
        fs = f(s);
        c = b; fc = fb;
        if(fa*fs < 0){ b=s; fb=fs; } else { a=s; fa=fs; }
        if(std::fabs(fa) < std::fabs(fb)){ std::swap(a,b); std::swap(fa,fb); }
        if(std::fabs(b-a) < xtol) break;
    }
    return b;
}

// -------- CSV I/O --------
struct Quote { double K, price; bool is_call; };

// 更鲁棒：自动跳过表头/注释/非数字行
inline std::vector<Quote> read_quotes_csv(const std::string& path){
    std::ifstream in(path);
    if(!in) throw std::runtime_error("Cannot open: "+path);
    std::vector<Quote> q;
    std::string line;
    auto is_numeric = [](const std::string& s){
        if(s.empty()) return false;
        char* end=nullptr; std::strtod(s.c_str(), &end); return end!=s.c_str();
    };
    while(std::getline(in,line)){
        if(line.empty()) continue;
        // 左侧 trim
        line.erase(line.begin(), std::find_if(line.begin(), line.end(),
            [](unsigned char ch){ return !std::isspace(ch); }));
        if(line.empty() || line[0]=='#') continue;

        std::stringstream ss(line);
        std::string sK, sp, st;
        if(!std::getline(ss,sK,',')) continue;
        if(!std::getline(ss,sp,',')) continue;
        if(!std::getline(ss,st,',')) st="put";

        if(!is_numeric(sK) || !is_numeric(sp)) continue; // 跳过表头/垃圾行

        Quote x;
        x.K = std::stod(sK);
        x.price = std::stod(sp);
        std::transform(st.begin(), st.end(), st.begin(), ::tolower);
        x.is_call = (st.find("call")!=std::string::npos);
        q.push_back(x);
    }
    return q;
}

inline void write_csv(const std::string& path,
                      const std::vector<double>& K,
                      const std::vector<double>& y,
                      const std::string& colname){
    std::ofstream out(path);
    if(!out) throw std::runtime_error("Cannot write: "+path);
    // 写表头，方便下游工具
    out << "Strike," << colname << "\n";
    for(size_t i=0;i<K.size();++i){
        if(std::isnan(y[i])) continue;
        out << K[i] << "," << y[i] << "\n";
    }
}

// -------- Cubic LS: iv ≈ a + b x + c x^2 + d x^3, x=K/S-1 --------
struct PolyCoef { double a,b,c,d; };
inline PolyCoef fit_cubic_poly(const std::vector<double>& K,
                               const std::vector<double>& iv,
                               double S){
    double Sx=0,Sx2=0,Sx3=0,Sx4=0,Sx5=0,Sx6=0;
    double Sy=0,Sxy=0,Sx2y=0,Sx3y=0; int n=0;
    for(size_t i=0;i<K.size();++i){
        double y=iv[i];
        if(std::isnan(y) || y<=0) continue;
        double x = K[i]/S - 1.0;
        double x2=x*x, x3=x2*x, x4=x3*x, x5=x4*x, x6=x5*x;
        Sx+=x; Sx2+=x2; Sx3+=x3; Sx4+=x4; Sx5+=x5; Sx6+=x6;
        Sy+=y; Sxy+=x*y; Sx2y+=x2*y; Sx3y+=x3*y; ++n;
    }
    if(n<6) throw std::runtime_error("Not enough points for cubic fit.");

    double M[4][4] = {
        { (double)n, Sx,   Sx2,  Sx3 },
        { Sx,        Sx2,  Sx3,  Sx4 },
        { Sx2,       Sx3,  Sx4,  Sx5 },
        { Sx3,       Sx4,  Sx5,  Sx6 }
    };
    double rhs[4] = { Sy, Sxy, Sx2y, Sx3y };

    // Gaussian elimination
    for(int i=0;i<4;++i){
        int piv=i;
        for(int r=i+1;r<4;++r) if(std::fabs(M[r][i])>std::fabs(M[piv][i])) piv=r;
        if(piv!=i){ for(int c=0;c<4;++c) std::swap(M[i][c], M[piv][c]); std::swap(rhs[i], rhs[piv]); }
        double diag = M[i][i];
        if(std::fabs(diag)<1e-12) throw std::runtime_error("Singular matrix in poly fit.");
        for(int c=i;c<4;++c) M[i][c]/=diag; rhs[i]/=diag;
        for(int r=0;r<4;++r){
            if(r==i) continue;
            double f = M[r][i];
            for(int c=i;c<4;++c) M[r][c]-=f*M[i][c];
            rhs[r]-=f*rhs[i];
        }
    }
    return {rhs[0], rhs[1], rhs[2], rhs[3]};
}
inline std::vector<double> eval_cubic_poly(const std::vector<double>& K, const PolyCoef& c, double S){
    std::vector<double> y(K.size(), std::numeric_limits<double>::quiet_NaN());
    for(size_t i=0;i<K.size();++i){
        double x = K[i]/S - 1.0;
        y[i] = c.a + c.b*x + c.c*x*x + c.d*x*x*x;
    }
    return y;
}

} // namespace qx
