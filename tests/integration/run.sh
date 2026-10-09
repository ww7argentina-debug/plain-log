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
category_id=$(wp term create category 'CI Category Alpha' --slug=ci-category-alpha --porcelain)
tag_id=$(wp term create post_tag 'CI Tag Alpha' --slug=ci-tag-alpha --porcelain)
categories_page_id=$(wp post create --post_type=page --post_status=publish --post_name=categories --post_title='CI Categories index' --post_content=$'<!--nextpage-->\n<p>CI_CATEGORY_PAGE_TWO</p>' --porcelain)
tags_page_id=$(wp post create --post_type=page --post_status=publish --post_name=tags --post_title='CI Tags index' --post_content=$'<p>CI_TAG_PAGE_ONE</p>\n<!--nextpage-->\n<!--nextpage-->\n<p>CI_TAG_PAGE_THREE</p>' --porcelain)
if [[ ! "$post_id" =~ ^[0-9]+$ || ! "$page_id" =~ ^[0-9]+$ || ! "$category_id" =~ ^[0-9]+$ || ! "$tag_id" =~ ^[0-9]+$ || ! "$categories_page_id" =~ ^[0-9]+$ || ! "$tags_page_id" =~ ^[0-9]+$ ]]; then
  echo 'WP-CLI did not return numeric test post, page, or term IDs.' >&2
  exit 1
fi
wp post term add "$post_id" category "$category_id"
wp post term add "$post_id" post_tag "$tag_id"

post_url=$(wp post url "$post_id")
page_url=$(wp post url "$page_id")
categories_url=$(wp post url "$categories_page_id")
tags_url=$(wp post url "$tags_page_id")
echo "WordPress: $(wp core version)"
echo "Web PHP: $("${compose[@]}" exec -T wordpress php -r 'echo PHP_VERSION;')"
echo "Test post ID: $post_id; test page IDs: $page_id, $categories_page_id, $tags_page_id"
python3 tests/integration/check_http.py "$site_url" "$post_url" "$page_url" "$categories_url" "$tags_url"

wp post update "$categories_page_id" --post_content='<p>CI_CATEGORY_PLAIN_CONTENT</p>'
wp post update "$tags_page_id" --post_content='<p>CI_TAG_PLAIN_CONTENT</p>'
python3 tests/integration/check_http.py --plain-index "$site_url" "$categories_url" "$tags_url"

wp post update "$categories_page_id" --post_content=$'<p>CI_CATEGORY_SECRET_ONE</p>\n<!--nextpage-->\n<p>CI_CATEGORY_SECRET_TWO</p>' --post_password=ci-only-password
wp post update "$tags_page_id" --post_content=$'<p>CI_TAG_SECRET_ONE</p>\n<!--nextpage-->\n<p>CI_TAG_SECRET_TWO</p>' --post_password=ci-only-password
python3 tests/integration/check_http.py --protected-index "$site_url" "$categories_url" "$tags_url"
