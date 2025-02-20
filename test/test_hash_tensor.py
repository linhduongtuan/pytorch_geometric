import pytest
import torch

from torch_geometric import HashTensor
from torch_geometric.testing import has_package, withCUDA

KEY_DTYPES = [
    torch.bool,
    torch.uint8,
    torch.int8,
    torch.int16,
    torch.int32,
    torch.int64,
    torch.float16,
    torch.bfloat16,
    torch.float32,
    torch.float64,
]


@withCUDA
@pytest.mark.skipif(
    not has_package('pyg-lib') and not has_package('pandas'),
    reason='Missing dependencies',
)
@pytest.mark.parametrize('dtype', KEY_DTYPES)
def test_basic(dtype, device):
    if dtype != torch.bool:
        key = torch.tensor([2, 1, 0], dtype=dtype, device=device)
    else:
        key = torch.tensor([True, False], device=device)
    value = torch.randn(key.size(0), 2, device=device)

    HashTensor(key, value)


@withCUDA
@pytest.mark.skipif(
    not has_package('pyg-lib') and not has_package('pandas'),
    reason='Missing dependencies',
)
def test_string_key(device):
    HashTensor(['1', '2', '3'], device=device)


@withCUDA
@pytest.mark.skipif(
    not has_package('pyg-lib') and not has_package('pandas'),
    reason='Missing dependencies',
)
def test_to_function(device):
    key = torch.tensor([2, 1, 0], device=device)
    value = torch.randn(key.size(0), 2, device=device)
    tensor = HashTensor(key, value)

    out = tensor.to(device)
    assert isinstance(out, HashTensor)
    assert id(out) == id(tensor)
    assert out.device == device
    assert out._value.device == device
    assert out._min_key.device == device
    assert out._max_key.device == device

    out = tensor.to('cpu')
    assert isinstance(out, HashTensor)
    if key.is_cuda:
        assert id(out) != id(tensor)
    else:
        assert id(out) == id(tensor)
    assert out.device == torch.device('cpu')
    assert out._value.device == torch.device('cpu')
    assert out._min_key.device == torch.device('cpu')
    assert out._max_key.device == torch.device('cpu')

    out = tensor.double()
    assert isinstance(out, HashTensor)
    assert out._value.dtype == torch.double


@withCUDA
@pytest.mark.skipif(
    not has_package('pyg-lib') and not has_package('pandas'),
    reason='Missing dependencies',
)
def test_unsqueeze(device):
    key = torch.tensor([2, 1, 0], device=device)
    tensor = HashTensor(key)

    with pytest.raises(IndexError, match="in the first dimension"):
        tensor.unsqueeze(0)

    with pytest.raises(IndexError, match="in the first dimension"):
        tensor.unsqueeze(-2)

    with pytest.raises(IndexError, match="out of range"):
        tensor.unsqueeze(2)

    with pytest.raises(IndexError, match="out of range"):
        tensor.unsqueeze(-3)

    out = tensor.unsqueeze(-1)
    assert out.size() == (3, 1)
    assert out._value is not None

    out = tensor[..., None]
    assert out.size() == (3, 1)
    assert out._value is not None

    out = tensor[..., None, None]
    assert out.size() == (3, 1, 1)
    assert out._value is not None

    value = torch.randn(key.size(0), 2, device=device)
    tensor = HashTensor(key, value)

    out = tensor.unsqueeze(-1)
    assert out.size() == (3, 2, 1)
    assert out._value is not None

    out = tensor[..., None]
    assert out.size() == (3, 2, 1)
    assert out._value is not None

    out = tensor[..., None, None]
    assert out.size() == (3, 2, 1, 1)
    assert out._value is not None

    out = tensor.unsqueeze(1)
    assert out.size() == (3, 1, 2)
    assert out._value is not None


@withCUDA
@pytest.mark.skipif(
    not has_package('pyg-lib') and not has_package('pandas'),
    reason='Missing dependencies',
)
@pytest.mark.parametrize('num_keys', [3, 1])
def test_squeeze(num_keys, device):
    key = torch.tensor([2, 1, 0][:num_keys], device=device)
    tensor = HashTensor(key)

    out = tensor.squeeze()
    assert isinstance(out, HashTensor)
    assert out.size() == (num_keys, )

    out = tensor.squeeze(0)
    assert isinstance(out, HashTensor)
    assert out.size() == (num_keys, )

    out = tensor.squeeze(-1)
    assert isinstance(out, HashTensor)
    assert out.size() == (num_keys, )

    out = tensor.squeeze([0])
    assert isinstance(out, HashTensor)
    assert out.size() == (num_keys, )

    with pytest.raises(IndexError, match="out of range"):
        tensor.squeeze(1)

    with pytest.raises(IndexError, match="out of range"):
        tensor.squeeze(-2)

    value = torch.randn(key.size(0), 1, 1, device=device)
    tensor = HashTensor(key, value)

    out = tensor.squeeze()
    assert isinstance(out, HashTensor)
    assert out.size() == (num_keys, )

    out = tensor.squeeze(0)
    assert isinstance(out, HashTensor)
    assert out.size() == (num_keys, 1, 1)

    out = tensor.squeeze(-1)
    assert isinstance(out, HashTensor)
    assert out.size() == (num_keys, 1)

    out = tensor.squeeze([0, 1, 2])
    assert isinstance(out, HashTensor)
    assert out.size() == (num_keys, )


@withCUDA
@pytest.mark.skipif(
    not has_package('pyg-lib') and not has_package('pandas'),
    reason='Missing dependencies',
)
def test_slice(device):
    key = torch.tensor([2, 1, 0], device=device)
    tensor = HashTensor(key)

    with pytest.raises(IndexError, match="out of range"):
        torch.narrow(tensor, dim=-2, start=0, length=2)

    out = tensor[-2:4]
    assert not isinstance(out, HashTensor)
    assert out.equal(torch.tensor([1, 2], device=device))

    out = tensor[..., 0:2]
    assert not isinstance(out, HashTensor)
    assert out.equal(torch.tensor([0, 1], device=device))

    out = torch.narrow(tensor, dim=0, start=2, length=1)
    assert not isinstance(out, HashTensor)
    assert out.equal(torch.tensor([2], device=device))

    out = tensor.narrow(dim=0, start=1, length=2)
    assert not isinstance(out, HashTensor)
    assert out.equal(torch.tensor([1, 2], device=device))

    value = torch.randn(key.size(0), 4, device=device)
    tensor = HashTensor(key, value)

    out = tensor[..., 0:2]
    assert isinstance(out, HashTensor)
    assert out.as_tensor().equal(value[..., 0:2])

    out = torch.narrow(tensor, dim=1, start=2, length=1)
    assert isinstance(out, HashTensor)
    assert out.as_tensor().equal(value[..., 2:3])
