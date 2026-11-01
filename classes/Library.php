<?php

namespace Grav\Plugin\ComponentLibrary;

use Grav\Common\Yaml;

/**
 * Reads the patterns/ folder and checks manifests. Used by the CLI commands;
 * nothing here runs on page requests.
 */
class Library
{
    public const LEVELS = ['theme', 'page', 'page-type', 'system'];
    public const REPO = 'Subschema-LLC/grav-plugin-component-library';
    public const BRANCH = 'main';

    /** @var string */
    private $root;

    public function __construct(?string $root = null)
    {
        $this->root = rtrim($root ?? \dirname(__DIR__), '/');
    }

    /** array_is_list() for PHP < 8.1 (Grav 1.7 sites). */
    private static function isList(array $a): bool
    {
        return $a === [] || array_keys($a) === range(0, \count($a) - 1);
    }

    public function root(): string
    {
        return $this->root;
    }

    /**
     * @return array<string, array{dir: string, manifest: array}>  keyed by pattern id
     */
    public function patterns(): array
    {
        $out = [];
        foreach (self::LEVELS as $level) {
            foreach (glob("{$this->root}/patterns/{$level}/*/pattern.yaml") ?: [] as $file) {
                $dir = \dirname($file);
                $id = $level . '/' . basename($dir);
                $out[$id] = ['dir' => $dir, 'manifest' => (array) Yaml::parse((string) file_get_contents($file))];
            }
        }
        ksort($out);

        return $out;
    }

    /**
     * Build the normalized catalog entry for a pattern id and manifest.
     */
    public function entry(string $id, ?array $m = null): array
    {
        if ($m === null) {
            $patterns = $this->patterns();
            $m = $patterns[$id]['manifest'] ?? [];
        }
        $rel = "patterns/{$id}";
        $listed = [];
        foreach ((array) ($m['files'] ?? []) as $value) {
            foreach ((array) $value as $f) {
                $listed[] = "{$rel}/{$f}";
            }
        }

        return [
            'id' => $id,
            'name' => $m['name'],
            'version' => $m['version'],
            'level' => $m['level'],
            'touches' => $m['touches'] ?? [],
            'status' => $m['status'],
            'summary' => $m['summary'],
            'use_when' => $m['use_when'] ?? [],
            'avoid_when' => $m['avoid_when'] ?? [],
            'compatibility' => $m['compatibility'],
            'requires' => $m['requires'] ?? new \stdClass(),
            'data' => $m['data'] ?? null,
            'legacy_keys' => $m['legacy_keys'] ?? [],
            'import' => isset($m['files']['blueprint'])
                ? ['type' => $id . '/' . preg_replace('/\.yaml$/', '', $m['files']['blueprint']), 'context' => 'plugin://component-library/patterns']
                : null,
            'include' => isset($m['files']['template']) ? "{$rel}/{$m['files']['template']}" : null,
            'apply' => $m['apply'],
            'classes' => $m['classes'] ?? null,
            'solves' => $m['solves'],
            'verify' => $m['verify'],
            'path' => $rel,
            'readme' => "{$rel}/README.md",
            'manifest' => "{$rel}/pattern.yaml",
            'files' => $listed,
            'raw_base' => 'https://raw.githubusercontent.com/' . self::REPO . '/' . self::BRANCH . "/{$rel}/",
        ];
    }

    /**
     * Find a pattern by its full id (page/tiles), its short folder name (tiles),
     * or its human title. Returns null when not found or ambiguous.
     */
    public function find(string $query): ?array
    {
        $query = trim($query, "/ \t\n\r\0\x0B");
        if ($query === '') {
            return null;
        }
        $patterns = $this->patterns();
        if (isset($patterns[$query])) {
            return $this->entry($query, $patterns[$query]['manifest']);
        }
        $matches = [];
        foreach ($patterns as $id => ['manifest' => $m]) {
            if (basename($id) === $query || strcasecmp((string) ($m['name'] ?? ''), $query) === 0) {
                $matches[$id] = $m;
            }
        }
        if (\count($matches) === 1) {
            $id = (string) array_key_first($matches);
            return $this->entry($id, $matches[$id]);
        }

        return null;
    }

    /**
     * Filter patterns by level and/or case-insensitive search terms matched
     * against id, name, summary, use_when, data keys and solved problems.
     *
     * @return list<array>
     */
    public function search(?string $level = null, ?string $query = null): array
    {
        $level = $level !== null && trim($level) !== '' ? trim($level) : null;
        $terms = $query !== null && trim($query) !== '' ? (preg_split('/\s+/', mb_strtolower(trim($query))) ?: []) : [];
        $out = [];
        foreach ($this->patterns() as $id => ['manifest' => $m]) {
            if ($level !== null && ($m['level'] ?? '') !== $level) {
                continue;
            }
            if ($terms) {
                $haystack = mb_strtolower(implode(' ', [
                    $id,
                    (string) ($m['name'] ?? ''),
                    (string) ($m['summary'] ?? ''),
                    implode(' ', (array) ($m['use_when'] ?? [])),
                    implode(' ', array_keys((array) ($m['data']['keys'] ?? []))),
                    implode(' ', array_map(static fn ($s) => ($s['problem'] ?? '') . ' ' . ($s['fix'] ?? ''), (array) ($m['solves'] ?? []))),
                ]));
                foreach ($terms as $term) {
                    if ($term !== '' && mb_strpos($haystack, $term) === false) {
                        continue 2;
                    }
                }
            }
            $out[] = $this->entry($id, $m);
        }

        return $out;
    }

    /**
     * Build copy-mode instructions (when using a pattern without installing the
     * plugin): which files to copy into a theme and the adjusted apply snippets.
     *
     * @return array{copy_files: list<array{from: string, to: string}>, apply: array<string, string>}
     */
    public function copyMode(array $entry): array
    {
        $id = (string) ($entry['id'] ?? '');
        $slug = basename($id);
        $rel = "patterns/{$id}";
        $copies = [];

        foreach ((array) ($entry['files'] ?? []) as $file) {
            $name = basename($file);
            if (substr($name, -5) === '.twig') {
                $copies[] = ['from' => $file, 'to' => "user/themes/<theme>/templates/{$file}"];
            } elseif ($name === 'blueprint.yaml' || $name === 'fields.yaml') {
                $copies[] = ['from' => $file, 'to' => "user/themes/<theme>/blueprints/partials/{$slug}.yaml"];
            } elseif ($name === 'page.yaml') {
                $copies[] = ['from' => $file, 'to' => "user/themes/<theme>/blueprints/partials/{$slug}-page.yaml"];
            } elseif (substr($name, -5) === '.yaml' && strpos($name, 'blueprint') !== false) {
                $copies[] = ['from' => $file, 'to' => "user/themes/<theme>/blueprints/{$slug}.yaml"];
            } elseif (substr($name, -3) === '.js' || substr($name, -4) === '.css') {
                $copies[] = ['from' => $file, 'to' => "user/themes/<theme>/{$file}"];
            }
        }
        $reqPatterns = (array) (($entry['requires'] instanceof \stdClass ? (array) $entry['requires'] : ($entry['requires'] ?? []))['patterns'] ?? []);
        if (\in_array('_shared/macros', $reqPatterns, true)) {
            $copies[] = [
                'from' => 'patterns/_shared/macros.html.twig',
                'to' => 'user/themes/<theme>/templates/patterns/_shared/macros.html.twig',
            ];
        }

        $apply = [];
        foreach ((array) ($entry['apply'] ?? []) as $kind => $snippet) {
            $converted = (string) $snippet;
            if ($kind === 'blueprint') {
                $converted = (string) preg_replace(
                    '#type:\s*' . preg_quote($id, '#') . '/(?:blueprint|fields)\b#',
                    "type: partials/{$slug}",
                    $converted
                );
                $converted = (string) preg_replace(
                    '#type:\s*' . preg_quote($id, '#') . '/([a-z0-9-]+)#',
                    "type: partials/{$slug}-$1",
                    $converted
                );
                $converted = str_replace("context: 'plugin://component-library/patterns'", "context: 'theme://blueprints'", $converted);
            }
            $converted = str_replace("plugin://component-library/{$rel}/", "theme://{$rel}/", $converted);
            $converted = str_replace('plugin://component-library/', 'theme://', $converted);
            $apply[(string) $kind] = $converted;
        }

        return ['copy_files' => $copies, 'apply' => $apply];
    }

    public function schema(): array
    {
        return json_decode((string) file_get_contents("{$this->root}/schema/pattern.schema.json"), true);
    }

    /**
     * Validate a value against the subset of JSON Schema used by
     * schema/pattern.schema.json: type, required, properties,
     * additionalProperties, enum, pattern, minLength, items, minItems,
     * uniqueItems, minProperties.
     *
     * @return string[] error messages
     */
    public function validateSchema($value, array $schema, string $path = ''): array
    {
        $errors = [];
        $at = $path === '' ? '(root)' : $path;

        if (isset($schema['enum']) && !\in_array($value, $schema['enum'], true)) {
            return ["{$at}: must be one of " . implode(', ', array_map('json_encode', $schema['enum']))];
        }

        $type = $schema['type'] ?? null;
        if ($type === 'object') {
            if (!\is_array($value) || ($value !== [] && self::isList($value))) {
                return ["{$at}: must be a map"];
            }
            foreach ($schema['required'] ?? [] as $key) {
                if (!array_key_exists($key, $value)) {
                    $errors[] = "{$at}: missing required key '{$key}'";
                }
            }
            if (isset($schema['minProperties']) && \count($value) < $schema['minProperties']) {
                $errors[] = "{$at}: needs at least {$schema['minProperties']} entries";
            }
            foreach ($value as $key => $item) {
                $child = $path === '' ? (string) $key : "{$path}.{$key}";
                if (isset($schema['properties'][$key])) {
                    $errors = array_merge($errors, $this->validateSchema($item, $schema['properties'][$key], $child));
                } elseif (($schema['additionalProperties'] ?? true) === false) {
                    $errors[] = "{$at}: unknown key '{$key}'";
                } elseif (\is_array($schema['additionalProperties'] ?? null)) {
                    $errors = array_merge($errors, $this->validateSchema($item, $schema['additionalProperties'], $child));
                }
            }
        } elseif ($type === 'array') {
            if (!\is_array($value) || ($value !== [] && !self::isList($value))) {
                return ["{$at}: must be a list"];
            }
            if (isset($schema['minItems']) && \count($value) < $schema['minItems']) {
                $errors[] = "{$at}: needs at least {$schema['minItems']} items";
            }
            if (!empty($schema['uniqueItems']) && \count($value) !== \count(array_unique(array_map('serialize', $value)))) {
                $errors[] = "{$at}: items must be unique";
            }
            foreach ($value as $i => $item) {
                if (isset($schema['items'])) {
                    $errors = array_merge($errors, $this->validateSchema($item, $schema['items'], "{$path}[{$i}]"));
                }
            }
        } elseif ($type === 'string') {
            if (!\is_string($value)) {
                return ["{$at}: must be a string"];
            }
            if (isset($schema['minLength']) && mb_strlen($value) < $schema['minLength']) {
                $errors[] = "{$at}: is too short";
            }
            if (isset($schema['pattern']) && !preg_match('/' . str_replace('/', '\/', $schema['pattern']) . '/u', $value)) {
                $errors[] = "{$at}: '{$value}' does not match {$schema['pattern']}";
            }
        } elseif ($type === 'boolean' && !\is_bool($value)) {
            $errors[] = "{$at}: must be true or false";
        }

        return $errors;
    }

    /**
     * Line-based template checks (see patterns/system/template-hygiene/rules.md).
     *
     * @return array<int, array{file: string, line: int, rule: string, level: string, message: string}>
     */
    public function lintPath(string $path): array
    {
        $files = [];
        if (is_file($path)) {
            $files = [$path];
        } elseif (is_dir($path)) {
            $it = new \RecursiveIteratorIterator(new \RecursiveDirectoryIterator($path, \FilesystemIterator::SKIP_DOTS));
            foreach ($it as $f) {
                $name = $f->getPathname();
                if (preg_match('/\.twig$/', $name) && !preg_match('#/(vendor|node_modules|\.git)/#', $name)) {
                    $files[] = $name;
                }
            }
            sort($files);
        }

        $issues = [];
        foreach ($files as $file) {
            $issues = array_merge($issues, $this->lintSource((string) file_get_contents($file), $file));
        }

        return $issues;
    }

    public function lintSource(string $src, string $file): array
    {
        $issues = [];
        $add = function (int $offset, string $rule, string $level, string $message) use (&$issues, $src, $file) {
            $line = substr_count(substr($src, 0, $offset), "\n") + 1;
            $lineText = explode("\n", $src)[$line - 1] ?? '';
            if (preg_match('/lint-ignore:\s*([a-z0-9-, ]+)/', $lineText, $m) && \in_array($rule, array_map('trim', explode(',', $m[1])), true)) {
                return;
            }
            $issues[] = ['file' => $file, 'line' => $line, 'rule' => $rule, 'level' => $level, 'message' => $message];
        };

        // nested-comment: a {# inside a {# ... #} comment ends nothing and leaks the rest.
        $offset = 0;
        while (($start = strpos($src, '{#', $offset)) !== false) {
            $end = strpos($src, '#}', $start + 2);
            if ($end === false) {
                break;
            }
            $inner = strpos(substr($src, $start + 2, $end - $start - 2), '{#');
            if ($inner !== false) {
                $add($start + 2 + $inner, 'nested-comment', 'error', 'Twig comments do not nest; this {# ends the outer comment early.');
            }
            $offset = $end + 2;
        }

        // Strip Twig comments for the remaining rules.
        $code = preg_replace_callback('/\{#.*?#\}/s', fn ($m) => preg_replace('/[^\n]/', ' ', $m[0]), $src);

        // twig-in-html-comment
        if (preg_match_all('/<!--(.*?)-->/s', $code, $mm, PREG_OFFSET_CAPTURE)) {
            foreach ($mm[1] as [$body, $pos]) {
                if (preg_match('/\{\{|\{%/', $body)) {
                    $add($pos, 'twig-in-html-comment', 'error', 'Twig runs inside <!-- -->; use {# #} to comment Twig out.');
                }
            }
        }

        // multiple-extends
        if (preg_match_all('/\{%-?\s*extends\b/', $code, $mm, PREG_OFFSET_CAPTURE) && \count($mm[0]) > 1) {
            $add($mm[0][1][1], 'multiple-extends', 'error', 'More than one {% extends %} ("Multiple extends tags are forbidden").');
        }

        // unescaped-header: {{ page.header.x }} / {{ header.x }} with no filter at all
        if (preg_match_all('/\{\{-?\s*((?:page\.)?header\.[A-Za-z0-9_.\[\]\'"]+)\s*-?\}\}/', $code, $mm, PREG_OFFSET_CAPTURE)) {
            foreach ($mm[1] as [$expr, $pos]) {
                $add($pos, 'unescaped-header', 'warning', "{$expr} is printed without |e; it is safe only while Twig autoescape stays on.");
            }
        }

        // theme-var-raw
        if (preg_match_all('/theme_var\([^)]*\)[^}]*\|\s*raw/', $code, $mm, PREG_OFFSET_CAPTURE)) {
            foreach ($mm[0] as [, $pos]) {
                $add($pos, 'theme-var-raw', 'error', "theme_var() is printed with |raw, but page front matter can override theme_var(); read trusted HTML with grav.config.get('theme.<key>').");
            }
        }
        // ...and a variable set from theme_var() later printed raw
        if (preg_match_all('/\{%-?\s*set\s+(\w+)\s*=\s*theme_var\(/', $code, $mm)) {
            foreach (array_unique($mm[1]) as $var) {
                if (preg_match('/\{\{-?\s*' . preg_quote($var, '/') . '\s*\|\s*raw/', $code, $m2, PREG_OFFSET_CAPTURE)) {
                    $add($m2[0][1], 'theme-var-raw', 'error', "'{$var}' comes from theme_var() and is printed with |raw; page front matter can override it.");
                }
            }
        }

        // blank-without-rel
        if (preg_match_all('/<a\b[^>]*target="_blank"[^>]*>/', $code, $mm, PREG_OFFSET_CAPTURE)) {
            foreach ($mm[0] as [$tag, $pos]) {
                if (strpos($tag, 'noopener') === false) {
                    $add($pos, 'blank-without-rel', 'warning', 'target="_blank" without rel="noopener noreferrer".');
                }
            }
        }

        // json-without-hex-tag: json_encode inside a <script> element without flags that include JSON_HEX_TAG (1)
        if (preg_match_all('/<script\b[^>]*>(.*?)<\/script>/s', $code, $mm, PREG_OFFSET_CAPTURE)) {
            foreach ($mm[1] as [$body, $pos]) {
                if (preg_match_all('/json_encode(?:\((\d*)\))?/', $body, $jm, PREG_OFFSET_CAPTURE)) {
                    foreach ($jm[1] as $i => $flag) {
                        $flags = (int) ($flag[0] ?? 0);
                        if (($flags & 1) === 0) {
                            $add($pos + $jm[0][$i][1], 'json-without-hex-tag', 'warning', 'json_encode inside <script> without JSON_HEX_TAG; use json_encode(15) or json_encode(321).');
                        }
                    }
                }
            }
        }

        // twig1-syntax
        foreach (['/\{%-?\s*filter\s+\w/' => '{% filter %} was removed in Twig 3; use {% apply %}.',
                  '/\{%-?\s*spaceless\b/' => '{% spaceless %} was removed in Twig 3; use the spaceless filter with {% apply %}.',
                  '/\{%-?\s*for\s+[^%]+\s+in\s+[^%]+\s+if\s+/' => '"for ... if" was removed in Twig 3; put an {% if %} inside the loop.'] as $re => $msg) {
            if (preg_match_all($re, $code, $mm, PREG_OFFSET_CAPTURE)) {
                foreach ($mm[0] as [, $pos]) {
                    $add($pos, 'twig1-syntax', 'error', $msg);
                }
            }
        }

        // media-url-true: media.url(true) looks absolute but is not (the argument is $reset)
        if (preg_match_all('/media\[[^\]]+\]\.url\(\s*true\s*\)|media\.url\(\s*true\s*\)/', $code, $mm, PREG_OFFSET_CAPTURE)) {
            foreach ($mm[0] as [, $pos]) {
                $add($pos, 'media-url-true', 'warning', "A media object's url(true) is not an absolute URL (the argument means reset); use url(media.url, true).");
            }
        }

        // lazy-header-image
        if (preg_match_all('/header_image[^}\n]*\.loading\(\s*[\'"]lazy[\'"]\s*\)/', $code, $mm, PREG_OFFSET_CAPTURE)) {
            foreach ($mm[0] as [, $pos]) {
                $add($pos, 'lazy-header-image', 'warning', "The header image is usually the page's Largest Contentful Paint; load it eagerly with fetchpriority('high').");
            }
        }

        // dropdown-always-open: Bulma's .navbar-item.has-dropdown.is-active forces .navbar-dropdown open permanently
        $activeVars = [];
        if (preg_match_all('/\{%-?\s*set\s+(\w+)\s*=[^%]*\bis-active\b[^%]*%\}/', $code, $mm)) {
            $activeVars = array_unique($mm[1]);
        }
        if (preg_match_all('/<[a-z0-9]+\b[^>]*class="[^"]*\bhas-dropdown\b[^"]*"[^>]*>/i', $code, $mm, PREG_OFFSET_CAPTURE)) {
            foreach ($mm[0] as [$tag, $pos]) {
                $hasActive = (bool) preg_match('/\bis-active\b/', $tag);
                if (!$hasActive) {
                    foreach ($activeVars as $var) {
                        if (preg_match('/\{\{[^}]*\b' . preg_quote($var, '/') . '\b[^}]*\}\}/', $tag)) {
                            $hasActive = true;
                            break;
                        }
                    }
                }
                if ($hasActive) {
                    $add($pos, 'dropdown-always-open', 'warning', "is-active on a Bulma .has-dropdown element forces its .navbar-dropdown flyout to stay open permanently on active pages; put is-active on the inner .navbar-link instead.");
                }
            }
        }

        usort($issues, fn ($a, $b) => $a['line'] <=> $b['line']);

        return $issues;
    }
}
