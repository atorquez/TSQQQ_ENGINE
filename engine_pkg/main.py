from engine_pkg.engine import get_5d_return, decide_ratio

BUDGET = 1000

def main():
    ret_tqqq, price_tqqq = get_5d_return("TQQQ")
    ret_sqqq, price_sqqq = get_5d_return("SQQQ")

    ratio_t, ratio_s = decide_ratio(ret_tqqq, ret_sqqq)

    alloc_t = BUDGET * ratio_t
    alloc_s = BUDGET * ratio_s

    shares_t = alloc_t // price_tqqq
    shares_s = alloc_s // price_sqqq

    print("\n=== TQQQ/SQQQ Simple Engine ===")
    print(f"5-day return TQQQ: {ret_tqqq:.2%}")
    print(f"5-day return SQQQ: {ret_sqqq:.2%}")
    print(f"\nRecommended ratio:")
    print(f"TQQQ: {ratio_t*100:.0f}%  (${alloc_t:.2f})")
    print(f"SQQQ: {ratio_s*100:.0f}%  (${alloc_s:.2f})")
    print(f"\nApprox shares:")
    print(f"TQQQ: {int(shares_t)} shares")
    print(f"SQQQ: {int(shares_s)} shares")

if __name__ == "__main__":
    main()