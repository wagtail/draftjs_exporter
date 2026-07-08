# Fallback components

When dealing with changes in the content schema, as part of ongoing development or migrations, some content can go stale.
To solve this, the exporter allows the definition of fallback components for blocks, styles, and entities.
This feature is only used for development at the moment, if you have a use case for this in production we would love to hear from you.
Please get in touch!

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

This fallback component can now control the exporter behavior when normal components are not found. Here is an example:

```python
def block_fallback(props):
    type_ = props['block']['type']

    if type_ == 'example-discard':
        logging.warning(f'Missing config for "{type_}". Discarding block, keeping content.')
        # Directly return the block's children to keep its content.
        return props['children']
    elif type_ == 'example-delete':
        logging.error(f'Missing config for "{type_}". Deleting block.')
        # Return None to not render anything, removing the whole block.
        return None
    else:
        logging.warning(f'Missing config for "{type_}". Using div instead.')
        # Provide a fallback.
        return DOM.create_element('div', {}, props['children'])
```

See [`examples.py`](https://github.com/wagtail/draftjs_exporter/blob/main/example.py) in the repository for more details.
