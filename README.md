# ChaosVM Executor

A Python envirionment for Tencent ChaosVM.

## Usage

```python
from chaosvm import execute

tdc = execute(vmjs, mouse_track=[(50, 42), (50, 55)])
print( tdc.getInfo().__dict__ )     # a python dict
print( tdc.getData(None, True) )    # a python str
```

## License

- AGPL-3.0
