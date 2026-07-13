<?php
/**
 * Plugin Name: LEDAJANS RankMath REST Enable
 * Description: Rank Math title/description/focus alanlarini WP REST ile guncellemek icin (sayfa + yazi).
 * Version: 1.0.0
 */

if (!defined('ABSPATH')) {
    exit;
}

add_action('init', function () {
    $keys = array(
        'rank_math_title'           => 'Rank Math SEO title',
        'rank_math_description'     => 'Rank Math meta description',
        'rank_math_focus_keyword'   => 'Rank Math focus keyword(s)',
        'rank_math_pillar_content'  => 'Rank Math cornerstone (pillar) flag',
    );
    foreach (array('post', 'page') as $object_type) {
        foreach ($keys as $key => $description) {
            $type = ($key === 'rank_math_pillar_content') ? 'string' : 'string';
            register_post_meta(
                $object_type,
                $key,
                array(
                    'type'              => $type,
                    'description'       => $description,
                    'single'            => true,
                    'show_in_rest'      => true,
                    'sanitize_callback' => 'sanitize_text_field',
                    'auth_callback'     => function () {
                        return current_user_can('edit_posts');
                    },
                )
            );
        }
    }
});
