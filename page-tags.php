<?php
/**
 * Tags index Page template.
 *
 * @package Plain_Log
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header();
?>

<main id="primary" class="site-main">
	<?php
	while ( have_posts() ) :
		the_post();
		global $multipage;

		$page_title   = get_the_title();
		$page_content = get_the_content();
		$tag_items    = array();
		$tags         = get_tags(
			array(
				'hide_empty' => true,
				'orderby'    => 'name',
				'order'      => 'ASC',
			)
		);

		if ( '' === trim( $page_title ) ) {
			$page_title = __( 'Tags', 'plain-log' );
		}

		if ( ! is_wp_error( $tags ) ) {
			foreach ( $tags as $tag ) {
				$tag_url = get_tag_link( $tag->term_id );

				if ( ! is_wp_error( $tag_url ) ) {
					$tag_items[] = array(
						'name'  => $tag->name,
						'count' => $tag->count,
						'url'   => $tag_url,
					);
				}
			}
		}
		?>

		<article id="post-<?php the_ID(); ?>" <?php post_class( array( 'single-entry', 'taxonomy-index-page' ) ); ?>>
			<header class="single-entry-header">
				<h1 class="single-entry-title"><?php echo esc_html( $page_title ); ?></h1>
			</header>

			<?php if ( '' !== trim( $page_content ) || $multipage ) : ?>
				<div class="entry-content">
					<?php the_content(); ?>
					<?php
					wp_link_pages(
						array(
							'before' => sprintf(
								'<nav class="page-links" aria-label="%1$s"><span class="page-links-label">%2$s</span>',
								esc_attr__( 'Page navigation', 'plain-log' ),
								esc_html__( 'Pages:', 'plain-log' )
							),
							'after'  => '</nav>',
						)
					);
					?>
				</div>
			<?php endif; ?>

			<section class="taxonomy-index" aria-labelledby="tags-index-title">
				<h2 id="tags-index-title" class="screen-reader-text"><?php esc_html_e( 'Tags', 'plain-log' ); ?></h2>

				<?php if ( ! empty( $tag_items ) ) : ?>
					<ul class="taxonomy-index-list">
						<?php foreach ( $tag_items as $tag_item ) : ?>
							<li class="taxonomy-index-item">
								<a href="<?php echo esc_url( $tag_item['url'] ); ?>"><?php echo esc_html( $tag_item['name'] ); ?></a>
								<span class="taxonomy-index-count"><?php echo esc_html( number_format_i18n( $tag_item['count'] ) ); ?></span>
							</li>
						<?php endforeach; ?>
					</ul>
				<?php else : ?>
					<p><?php esc_html_e( 'No tags found.', 'plain-log' ); ?></p>
				<?php endif; ?>
			</section>
		</article>
	<?php endwhile; ?>
</main>

<?php
get_footer();
