#!/bin/bash
#SBATCH --job-name=b3-minimax-dl
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --nodelist=h100-sxm-8-0
#SBATCH --gres=gpu:0
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --output=/clusterhome/long_yi/score-seeking-b3/logs/slurm-dl-%j.out
#SBATCH --error=/clusterhome/long_yi/score-seeking-b3/logs/slurm-dl-%j.err

# Download-only job (no GPU) so we don't hog H100s while HF pulls weights.
# Reservation etiquette: tell Lucid before long GPU serve jobs; this DL is fine on shared login-adjacent node.

set -euo pipefail
mkdir -p /clusterhome/long_yi/score-seeking-b3/logs
bash /clusterhome/long_yi/score-seeking-b3/b3_vcf_bootstrap.sh
