# Fallback components

When dealing with changes in the content schema, as part of ongoing development or migrations, some content can go stale. To solve this, the exporter allows the definition of fallback components for blocks, styles, and entities. A fallback is just a regular [custom component](custom-components.md) wired to the special `BLOCK_TYPES.FALLBACK`, `INLINE_STYLES.FALLBACK`, or `ENTITY_TYPES.FALLBACK` key in your [configuration](../reference/configuration.md).

This feature is only used for development at the moment, if you have a use case for this in production we would love to hear from you. Please get in touch!

Add the following to the exporter config,

```python
config = {
    'block_map': {
        **BLOCK_MAP,
        # Provide a fallback for block types.
        BLOCK_TYPES.FALLBACK: block_fallback
    },
}
```

This fallback component can now control the exporter behavior when normal components are not found. A fallback receives the same `props` as any [custom component](custom-components.md), and can return one of three things:

- The block's `children` to keep the content but discard the wrapping element.
- `None` to remove the block entirely.
- Any DOM element to provide an alternative rendering.

```python
def block_fallback(props):
    type_ = props['block']['type']

    if type_ == 'example-discard':
        logging.warning(f'Missing config for "{type_}". Discarding block, keeping content.')
        return props['children']
    elif type_ == 'example-delete':
        logging.error(f'Missing config for "{type_}". Deleting block.')
        return None
    else:
        logging.warning(f'Missing config for "{type_}". Using div instead.')
        return DOM.create_element('div', {}, props['children'])
```

See [`example.py`](https://github.com/wagtail/draftjs_exporter/blob/main/example.py) in the repository for more details.
