#!/usr/bin/env bash
set -euo pipefail

# Run in a regular local terminal: bash publish_to_github.sh
# This creates a private repository and uploads the current project snapshot.
task_source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
task_repo_name="${1:-vps-project-docs}"
if [[ ! "$task_repo_name" =~ ^[A-Za-z0-9_.-]+$ ]]; then
  printf '%s\n' 'Недопустимое имя репозитория.' >&2
  exit 1
fi
for task_command in gh git python3; do
  command -v "$task_command" >/dev/null || { printf 'Не найдена команда: %s\n' "$task_command" >&2; exit 1; }
done
if ! gh auth status >/dev/null 2>&1; then
  printf '%s\n' 'Сначала войди в GitHub командой gh auth login и запусти скрипт повторно.' >&2
  exit 1
fi
task_login="$(gh api user --jq .login)"
task_remote="$task_login/$task_repo_name"
task_stage_dir="$(mktemp -d "${TMPDIR:-/tmp}/vps-github.XXXXXXXX")"
task_repo_dir="$task_stage_dir/repository"
# The snapshot stays available if creation or pushing fails.
printf 'Локальная копия для отправки: %s\n' "$task_repo_dir"
python3 - "$task_source_dir" "$task_repo_dir" <<'PY'
import shutil, sys
from pathlib import Path
source, target = map(Path, sys.argv[1:])
excluded = {'.git', '.aws', '.agents', '.codex', '__pycache__', 'GitHub_upload'}
def skip(folder, names):
    return [name for name in names if name in excluded or name.endswith('.pyc')]
shutil.copytree(source, target, ignore=skip)
PY
git -C "$task_repo_dir" init --initial-branch=main
git -C "$task_repo_dir" add --all
git -C "$task_repo_dir" -c user.name="$task_login" -c user.email="$task_login@users.noreply.github.com" commit -m "Add VPS project documents, examples, diagrams and editable sources"
task_repo_state="$(gh repo view "$task_remote" --json isPrivate,isEmpty --jq '[.isPrivate,.isEmpty] | @tsv' 2>/dev/null || true)"
if [[ -n "$task_repo_state" ]]; then
  if [[ "$task_repo_state" != $'true\ttrue' ]]; then
    printf 'Репозиторий %s уже существует и не является пустым приватным репозиторием. Ничего не перезаписано.\n' "$task_remote" >&2
    exit 1
  fi
else
  gh repo create "$task_remote" --private --description 'Проект VPS/VDS: документация, примеры, схемы и исходники редактирования'
fi
task_private="$(gh repo view "$task_remote" --json isPrivate --jq .isPrivate)"
[[ "$task_private" == true ]] || { printf '%s\n' 'Приватность репозитория не подтверждена; отправка остановлена.' >&2; exit 1; }
git -C "$task_repo_dir" remote add origin "https://github.com/$task_remote.git"
gh auth setup-git --hostname github.com
git -C "$task_repo_dir" push --set-upstream origin main
task_local_sha="$(git -C "$task_repo_dir" rev-parse HEAD)"
task_remote_sha="$(git -C "$task_repo_dir" ls-remote origin refs/heads/main | cut -f1)"
[[ "$task_local_sha" == "$task_remote_sha" ]] || { printf '%s\n' 'Не удалось подтвердить отправленный коммит.' >&2; exit 1; }
printf '\nГотово: https://github.com/%s (private)\n' "$task_remote"
printf 'На ноутбуке: gh repo clone %s\n' "$task_remote"
