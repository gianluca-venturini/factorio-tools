import argparse

from balancer import BALANCERS

def main():
    parser = argparse.ArgumentParser(description="Optimization tools for Factorio.")
    parser.add_argument('--solve_balancer', type=str, required=True, help="The name of the balancer to solve.")
    args = parser.parse_args()

    if args.solve_balancer:
        if args.solve_balancer not in BALANCERS:
            print(f"Balancer '{args.solve_balancer}' not found.")
            return
        BALANCERS[args.solve_balancer]()

if __name__ == "__main__":
    main()