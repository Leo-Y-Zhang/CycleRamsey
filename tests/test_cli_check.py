import argparse
import json

import pytest

from ramsey.__main__ import cmd_check


def write_witness(tmp_path, colouring='001'):
    path = tmp_path / 'witness.json'
    record = {'n': 3, 'targets': [3, 3, 3]}
    if colouring is not None:
        record['colouring'] = colouring
    path.write_text(json.dumps(record))
    return argparse.Namespace(witness=str(path))


def test_check_accepts_good_witness(tmp_path, capsys):
    assert cmd_check(write_witness(tmp_path)) == 0
    assert 'verdict: GOOD' in capsys.readouterr().out


def test_check_rejects_one_recoloured_edge(tmp_path, capsys):
    assert cmd_check(write_witness(tmp_path, '000')) == 1
    assert 'verdict: BAD' in capsys.readouterr().out


@pytest.mark.parametrize('colouring', ['00', '0010', ''])
def test_check_rejects_wrong_character_count(tmp_path, capsys, colouring):
    assert cmd_check(write_witness(tmp_path, colouring)) == 1
    assert 'MALFORMED' in capsys.readouterr().err


def test_check_rejects_record_without_witness(tmp_path, capsys):
    assert cmd_check(write_witness(tmp_path, None)) == 2
    assert 'no colouring' in capsys.readouterr().err


def test_check_rejects_invalid_colour(tmp_path, capsys):
    assert cmd_check(write_witness(tmp_path, '003')) == 1
    assert 'verdict: BAD' in capsys.readouterr().out


def test_check_rejects_truncated_json_file(tmp_path):
    args = write_witness(tmp_path)
    with open(args.witness, 'rb+') as stream:
        stream.truncate(20)
    with pytest.raises(json.JSONDecodeError):
        cmd_check(args)


def test_check_refuses_witness_that_cannot_fail_under_single_recolouring(tmp_path, capsys):
    assert cmd_check(write_witness(tmp_path, '012')) == 1
    assert 'verdict: SUSPECT' in capsys.readouterr().out
