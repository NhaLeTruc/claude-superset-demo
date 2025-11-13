#!/usr/bin/env python3
"""
Sample Data Generator for GoodNote Analytics Platform

Generates realistic sample data for testing Spark jobs and optimization analysis.
Creates two CSV files:
- user_interactions.csv: User interaction events
- user_metadata.csv: User demographic and device information

Usage:
    python scripts/generate_sample_data.py --num-users 1000 --num-interactions 10000
    python scripts/generate_sample_data.py --small   # 1K users, 10K interactions
    python scripts/generate_sample_data.py --medium  # 10K users, 100K interactions
    python scripts/generate_sample_data.py --large   # 100K users, 1M interactions
"""
import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# Constants
ACTION_TYPES = ["VIEW", "EDIT", "SHARE", "EXPORT"]
DEVICE_TYPES = ["iPhone", "iPad", "Android Phone", "Android Tablet"]
COUNTRIES = ["US", "UK", "CA", "DE", "FR", "JP", "AU", "CN", "IN", "BR"]
SUBSCRIPTION_TYPES = ["free", "premium", "enterprise"]
APP_VERSIONS = ["3.0.0", "3.0.1", "3.1.0", "3.1.1", "3.2.0"]

# Realistic distributions
DEVICE_DISTRIBUTION = {
    "iPhone": 0.40,
    "iPad": 0.25,
    "Android Phone": 0.25,
    "Android Tablet": 0.10
}

COUNTRY_DISTRIBUTION = {
    "US": 0.35,
    "UK": 0.10,
    "CA": 0.08,
    "DE": 0.08,
    "FR": 0.07,
    "JP": 0.10,
    "AU": 0.05,
    "CN": 0.08,
    "IN": 0.06,
    "BR": 0.03
}

SUBSCRIPTION_DISTRIBUTION = {
    "free": 0.60,
    "premium": 0.30,
    "enterprise": 0.10
}

VERSION_DISTRIBUTION = {
    "3.0.0": 0.10,
    "3.0.1": 0.15,
    "3.1.0": 0.25,
    "3.1.1": 0.30,
    "3.2.0": 0.20
}


def weighted_random_choice(distribution):
    """Choose item based on weighted distribution."""
    items = list(distribution.keys())
    weights = list(distribution.values())
    return random.choices(items, weights=weights, k=1)[0]


def generate_user_metadata(num_users):
    """Generate user metadata CSV."""
    print(f"📝 Generating metadata for {num_users:,} users...")

    users = []
    for user_id in range(1, num_users + 1):
        user = {
            "user_id": f"user_{user_id:06d}",
            "device_type": weighted_random_choice(DEVICE_DISTRIBUTION),
            "country": weighted_random_choice(COUNTRY_DISTRIBUTION),
            "subscription_type": weighted_random_choice(SUBSCRIPTION_DISTRIBUTION),
            "registration_date": (
                datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365))
            ).strftime("%Y-%m-%d")
        }
        users.append(user)

    print(f"   ✅ Generated {len(users):,} users")
    return users


def generate_user_interactions(num_interactions, users, include_skew=True):
    """
    Generate user interactions CSV.

    Args:
        num_interactions: Number of interactions to generate
        users: List of user metadata dicts
        include_skew: If True, create hot keys (20% of users generate 80% of interactions)
    """
    print(f"📝 Generating {num_interactions:,} interactions...")

    # Create user ID list with skew if requested
    user_ids = [u["user_id"] for u in users]

    if include_skew:
        # Create Pareto distribution: 20% of users generate 80% of interactions
        num_power_users = int(len(user_ids) * 0.20)
        power_users = random.sample(user_ids, num_power_users)
        normal_users = [uid for uid in user_ids if uid not in power_users]

        # 80% of interactions from power users
        power_user_interactions = int(num_interactions * 0.80)
        normal_user_interactions = num_interactions - power_user_interactions

        # Create weighted user pool
        user_pool = (
            power_users * (power_user_interactions // num_power_users) +
            normal_users * (normal_user_interactions // len(normal_users))
        )
        random.shuffle(user_pool)
        print(f"   📊 Data skew: {num_power_users:,} power users ({num_power_users/len(user_ids)*100:.1f}%) generate 80% of interactions")
    else:
        user_pool = user_ids * (num_interactions // len(user_ids) + 1)
        random.shuffle(user_pool)

    interactions = []
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range = (end_date - start_date).days

    for i in range(num_interactions):
        # Generate timestamp
        timestamp = start_date + timedelta(
            days=random.randint(0, date_range),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )

        # Generate duration (realistic distribution)
        # Most actions are quick (0-10 seconds)
        # Some are moderate (10-60 seconds)
        # Few are long (60-300 seconds)
        duration_category = random.random()
        if duration_category < 0.70:  # 70% quick
            duration_ms = random.randint(100, 10000)  # 0.1-10 seconds
        elif duration_category < 0.95:  # 25% moderate
            duration_ms = random.randint(10000, 60000)  # 10-60 seconds
        else:  # 5% long
            duration_ms = random.randint(60000, 300000)  # 1-5 minutes

        interaction = {
            "user_id": user_pool[i % len(user_pool)],
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "action_type": weighted_random_choice(
                {"VIEW": 0.50, "EDIT": 0.30, "SHARE": 0.15, "EXPORT": 0.05}
            ),
            "duration_ms": duration_ms,
            "app_version": weighted_random_choice(VERSION_DISTRIBUTION)
        }
        interactions.append(interaction)

        if (i + 1) % 100000 == 0:
            print(f"   ⏳ Generated {i + 1:,} / {num_interactions:,} interactions...")

    # Sort by timestamp for realistic data
    interactions.sort(key=lambda x: x["timestamp"])

    print(f"   ✅ Generated {len(interactions):,} interactions")
    return interactions


def write_csv(data, filename, fieldnames):
    """Write data to CSV file."""
    filepath = Path("data/raw") / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)

    print(f"💾 Writing to {filepath}...")
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    # Get file size
    size_mb = filepath.stat().st_size / (1024 * 1024)
    print(f"   ✅ Written {len(data):,} rows ({size_mb:.2f} MB)")


def main():
    parser = argparse.ArgumentParser(description="Generate sample data for GoodNote Analytics")

    # Preset sizes
    parser.add_argument("--small", action="store_true", help="Small dataset (1K users, 10K interactions)")
    parser.add_argument("--medium", action="store_true", help="Medium dataset (10K users, 100K interactions)")
    parser.add_argument("--large", action="store_true", help="Large dataset (100K users, 1M interactions)")

    # Custom sizes
    parser.add_argument("--num-users", type=int, help="Number of users to generate")
    parser.add_argument("--num-interactions", type=int, help="Number of interactions to generate")

    # Options
    parser.add_argument("--no-skew", action="store_true", help="Disable data skew (uniform distribution)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")

    args = parser.parse_args()

    # Set random seed
    random.seed(args.seed)
    print(f"🌱 Random seed: {args.seed}")

    # Determine sizes
    if args.small:
        num_users = 1000
        num_interactions = 10000
        print("📦 Small dataset selected")
    elif args.medium:
        num_users = 10000
        num_interactions = 100000
        print("📦 Medium dataset selected")
    elif args.large:
        num_users = 100000
        num_interactions = 1000000
        print("📦 Large dataset selected")
    elif args.num_users and args.num_interactions:
        num_users = args.num_users
        num_interactions = args.num_interactions
        print(f"📦 Custom dataset: {num_users:,} users, {num_interactions:,} interactions")
    else:
        # Default to small
        num_users = 1000
        num_interactions = 10000
        print("📦 Default (small) dataset selected")

    print(f"\n{'='*60}")
    print(f"Generating GoodNote Analytics Sample Data")
    print(f"{'='*60}\n")

    # Generate metadata
    users = generate_user_metadata(num_users)
    write_csv(
        users,
        "user_metadata.csv",
        ["user_id", "device_type", "country", "subscription_type", "registration_date"]
    )

    print()

    # Generate interactions
    interactions = generate_user_interactions(
        num_interactions,
        users,
        include_skew=not args.no_skew
    )
    write_csv(
        interactions,
        "user_interactions.csv",
        ["user_id", "timestamp", "action_type", "duration_ms", "app_version"]
    )

    print(f"\n{'='*60}")
    print("✅ Sample data generation complete!")
    print(f"{'='*60}\n")

    print("📁 Files created:")
    print("   • data/raw/user_interactions.csv")
    print("   • data/raw/user_metadata.csv")
    print("\n🚀 Ready to run Spark jobs!")
    print("   Run: ./src/jobs/run_all_jobs.sh\n")


if __name__ == "__main__":
    main()
