#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")/../.."

project="plainlog-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}"
compose=(docker compose --project-name "$project" --file tests/integration/compose.yml)

"${compose[@]}" version

cleanup() {
  result=$?
  trap - EXIT
  if (( result != 0 )); then
    "${compose[@]}" logs --no-color || true
  fi
  if ! "${compose[@]}" down --volumes --remove-orphans; then
    echo 'Failed to clean up the WordPress test containers.' >&2
    result=1
  fi
  exit "$result"
}
trap cleanup EXIT

"${compose[@]}" up --detach --wait db wordpress

ready=false
for attempt in {1..60}; do
  status=$(curl --silent --output /dev/null --write-out '%{http_code}' --max-time 3 'http://127.0.0.1:8080/wp-admin/install.php' || true)
  if [[ "$status" == 200 ]]; then
    ready=true
    break
  fi
  sleep 2
done
if [[ "$ready" != true ]]; then
  echo 'WordPress installer did not become available.' >&2
  exit 1
fi

"${compose[@]}" exec -T --user 33:33 wordpress mkdir -p /var/www/html/wp-content/themes/plain-log
git archive HEAD | "${compose[@]}" exec -T --user 33:33 wordpress tar -xf - -C /var/www/html/wp-content/themes/plain-log

wp() {
  "${compose[@]}" run --rm --no-deps -T cli "$@"
}

site_url='http://127.0.0.1:8080'
wp core install --url="$site_url" --title='Plain Log CI' --admin_user=ci-admin --admin_password=ci-only-password --admin_email=ci@example.invalid --skip-email
wp theme activate plain-log
wp theme is-active plain-log

post_id=$(wp post create --post_type=post --post_status=publish --post_title='CIUniqueTokenAlpha article' --post_content=$'<p>CI_POST_FIRST_PAGE</p>\n<!--nextpage-->\n<p>CI_POST_SECOND_PAGE</p>' --porcelain)
page_id=$(wp post create --post_type=page --post_status=publish --post_name=ci-paginated-page --post_title='CI paginated page' --post_content=$'<p>CI_PAGE_FIRST_PAGE</p>\n<!--nextpage-->\n<p>CI_PAGE_SECOND_PAGE</p>' --porcelain)
if [[ ! "$post_id" =~ ^[0-9]+$ || ! "$page_id" =~ ^[0-9]+$ ]]; then
  echo 'WP-CLI did not return numeric test post and page IDs.' >&2
  exit 1
fi

post_url=$(wp post url "$post_id")
page_url=$(wp post url "$page_id")
echo "WordPress: $(wp core version)"
echo "Web PHP: $("${compose[@]}" exec -T wordpress php -r 'echo PHP_VERSION;')"
echo "Test post ID: $post_id; test page ID: $page_id"
python3 tests/integration/check_http.py "$site_url" "$post_url" "$page_url"
