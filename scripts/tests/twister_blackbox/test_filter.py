#!/usr/bin/env python3
# Copyright (c) 2024 Intel Corporation
#
# SPDX-License-Identifier: Apache-2.0
"""
Blackbox tests for twister's command line functions related to test filtering.
"""

import importlib
import mock
import os
import pytest
import sys
import json
import re

from conftest import ZEPHYR_BASE, TEST_DATA, testsuite_filename_mock
from twisterlib.testplan import TestPlan


class TestFilter:
    TESTDATA_1 = [
        (
            'x86',
            [
                r'(it8xxx2_evb/it81302bx).*?(SKIPPED: Command line testsuite arch filter)',
            ],
        ),
        (
            'arm',
            [
                r'(it8xxx2_evb/it81302bx).*?(SKIPPED: Command line testsuite arch filter)',
                r'(qemu_x86/atom).*?(SKIPPED: Command line testsuite arch filter)',
                r'(hsdk/arc_hsdk).*?(SKIPPED: Command line testsuite arch filter)',
            ]
        ),
        (
            'riscv',
            [
                r'(qemu_x86/atom).*?(SKIPPED: Command line testsuite arch filter)',
                r'(hsdk/arc_hsdk).*?(SKIPPED: Command line testsuite arch filter)',            ]
        )
    ]
    TESTDATA_2 = [
        (
            'nxp',
            [
                r'(it8xxx2_evb/it81302bx).*?(SKIPPED: Not a selected vendor platform)',
                r'(hsdk/arc_hsdk).*?(SKIPPED: Not a selected vendor platform)',
                r'(qemu_x86).*?(SKIPPED: Not a selected vendor platform)',
            ],
        ),
        (
            'intel',
            [
                r'(it8xxx2_evb/it81302bx).*?(SKIPPED: Not a selected vendor platform)',
                r'(qemu_x86/atom).*?(SKIPPED: Not a selected vendor platform)',
                r'(DEBUG\s+- adding intel_adl_crb)'
            ]
        ),
        (
            'ite',
            [
                r'(qemu_x86/atom).*?(SKIPPED: Not a selected vendor platform)',
                r'(intel_adl_crb/alder_lake).*?(SKIPPED: Not a selected vendor platform)',
                r'(hsdk/arc_hsdk).*?(SKIPPED: Not a selected vendor platform)',
                r'(DEBUG\s+- adding it8xxx2_evb)'
            ]
        )
    ]

    @classmethod
    def setup_class(cls):
        apath = os.path.join(ZEPHYR_BASE, 'scripts', 'twister')
        cls.loader = importlib.machinery.SourceFileLoader('__main__', apath)
        cls.spec = importlib.util.spec_from_loader(cls.loader.name, cls.loader)
        cls.twister_module = importlib.util.module_from_spec(cls.spec)

    @classmethod
    def teardown_class(cls):
        pass

    @pytest.mark.parametrize(
        'tag, expected_test_count',
        [
            ('device', 5),   # dummy.agnostic.group1.subgroup1.assert
                             # dummy.agnostic.group1.subgroup2.assert
                             # dummy.agnostic.group2.assert1
                             # dummy.agnostic.group2.assert2
                             # dummy.agnostic.group2.assert3
            ('agnostic', 1)  # dummy.device.group.assert
        ],
        ids=['no device', 'no agnostic']
    )
    @mock.patch.object(TestPlan, 'TESTSUITE_FILENAME', testsuite_filename_mock)
    def test_exclude_tag(self, out_path, tag, expected_test_count):
        test_platforms = ['qemu_x86', 'intel_adl_crb']
        path = os.path.join(TEST_DATA, 'tests', 'dummy')
        args = ['-i', '--outdir', out_path, '-T', path, '-y'] + \
               ['--exclude-tag', tag] + \
               [val for pair in zip(
                   ['-p'] * len(test_platforms), test_platforms
               ) for val in pair]

        with mock.patch.object(sys, 'argv', [sys.argv[0]] + args), \
                pytest.raises(SystemExit) as sys_exit:
            self.loader.exec_module(self.twister_module)

        with open(os.path.join(out_path, 'testplan.json')) as f:
            j = json.load(f)
        filtered_j = [
            (ts['platform'], ts['name'], tc['identifier']) \
                for ts in j['testsuites'] \
                for tc in ts['testcases'] if 'reason' not in tc
        ]

        assert len(filtered_j) == expected_test_count

        assert str(sys_exit.value) == '0'

    @mock.patch.object(TestPlan, 'TESTSUITE_FILENAME', testsuite_filename_mock)
    def test_enable_slow(self, out_path):
        test_platforms = ['qemu_x86', 'intel_adl_crb']
        path = os.path.join(TEST_DATA, 'tests', 'dummy', 'agnostic')
        alt_config_root = os.path.join(TEST_DATA, 'alt-test-configs', 'dummy', 'agnostic')
        args = ['-i', '--outdir', out_path, '-T', path] + \
               ['--enable-slow'] + \
               ['--alt-config-root', alt_config_root] + \
               [val for pair in zip(
                   ['-p'] * len(test_platforms), test_platforms
               ) for val in pair]

        with mock.patch.object(sys, 'argv', [sys.argv[0]] + args), \
                pytest.raises(SystemExit) as sys_exit:
            self.loader.exec_module(self.twister_module)

        with open(os.path.join(out_path, 'testplan.json')) as f:
            j = json.load(f)
        filtered_j = [
            (ts['platform'], ts['name'], tc['identifier']) \
               for ts in j['testsuites'] \
               for tc in ts['testcases'] if 'reason' not in tc
        ]

        assert str(sys_exit.value) == '0'

        assert len(filtered_j) == 5

    @mock.patch.object(TestPlan, 'TESTSUITE_FILENAME', testsuite_filename_mock)
    def test_enable_slow_only(self, out_path):
        test_platforms = ['qemu_x86', 'intel_adl_crb']
        path = os.path.join(TEST_DATA, 'tests', 'dummy', 'agnostic')
        alt_config_root = os.path.join(TEST_DATA, 'alt-test-configs', 'dummy', 'agnostic')
        args = ['-i', '--outdir', out_path, '-T', path] + \
               ['--enable-slow-only'] + \
               ['--alt-config-root', alt_config_root] + \
               [val for pair in zip(
                   ['-p'] * len(test_platforms), test_platforms
               ) for val in pair]

        with mock.patch.object(sys, 'argv', [sys.argv[0]] + args), \
                pytest.raises(SystemExit) as sys_exit:
            self.loader.exec_module(self.twister_module)

        with open(os.path.join(out_path, 'testplan.json')) as f:
            j = json.load(f)
        filtered_j = [
            (ts['platform'], ts['name'], tc['identifier']) \
               for ts in j['testsuites'] \
               for tc in ts['testcases'] if 'reason' not in tc
        ]

        assert str(sys_exit.value) == '0'

        assert len(filtered_j) == 3

    @pytest.mark.parametrize(
        'arch, expected',
        TESTDATA_1,
        ids=[
            'arch x86',
            'arch arm',
            'arch riscv'
        ],
    )

    @mock.patch.object(TestPlan, 'TESTSUITE_FILENAME', testsuite_filename_mock)
    def test_arch(self, capfd, out_path, arch, expected):
        path = os.path.join(TEST_DATA, 'tests', 'no_filter')
        test_platforms = ['qemu_x86', 'hsdk', 'intel_adl_crb', 'it8xxx2_evb']
        args = ['--outdir', out_path, '-T', path, '-vv', '-ll', 'DEBUG'] + \
               ['--arch', arch] + \
               [val for pair in zip(
                   ['-p'] * len(test_platforms), test_platforms
               ) for val in pair]

        with mock.patch.object(sys, 'argv', [sys.argv[0]] + args), \
            pytest.raises(SystemExit) as sys_exit:
            self.loader.exec_module(self.twister_module)

        out, err = capfd.readouterr()
        sys.stdout.write(out)
        sys.stderr.write(err)

        assert str(sys_exit.value) == '0'

        for line in expected:
            print(err)
            assert re.search(line, err)

    @pytest.mark.parametrize(
        'vendor, expected',
        TESTDATA_2,
        ids=[
            'vendor nxp',
            'vendor intel',
            'vendor ite'
        ],
    )

    @mock.patch.object(TestPlan, 'TESTSUITE_FILENAME', testsuite_filename_mock)
    def test_vendor(self, capfd, out_path, vendor, expected):
        path = os.path.join(TEST_DATA, 'tests', 'no_filter')
        test_platforms = ['qemu_x86', 'hsdk', 'intel_adl_crb', 'it8xxx2_evb']
        args = ['--outdir', out_path, '-T', path, '-vv', '-ll', 'DEBUG'] + \
               ['--vendor', vendor] + \
               [val for pair in zip(
                   ['-p'] * len(test_platforms), test_platforms
               ) for val in pair]

        with mock.patch.object(sys, 'argv', [sys.argv[0]] + args), \
            pytest.raises(SystemExit) as sys_exit:
            self.loader.exec_module(self.twister_module)

        out, err = capfd.readouterr()
        sys.stdout.write(out)
        sys.stderr.write(err)

        for line in expected:
            assert re.search(line, err)

        assert str(sys_exit.value) == '0'

    @pytest.mark.parametrize(
        'flag, expected_test_count',
        [
            (['--ignore-platform-key'], 2),
            ([], 1)
        ],
        ids=['ignore_platform_key', 'without ignore_platform_key']
    )
    @mock.patch.object(TestPlan, 'TESTSUITE_FILENAME', testsuite_filename_mock)
    def test_ignore_platform_key(self, out_path, flag, expected_test_count):
        test_platforms = ['qemu_x86', 'qemu_x86_64']
        path = os.path.join(TEST_DATA, 'tests', 'platform_key')
        args = ['-i', '--outdir', out_path, '-T', path] + \
               flag + \
               [val for pair in zip(
                   ['-p'] * len(test_platforms), test_platforms
               ) for val in pair]

        with mock.patch.object(sys, 'argv', [sys.argv[0]] + args), \
            pytest.raises(SystemExit) as sys_exit:
            self.loader.exec_module(self.twister_module)

        with open(os.path.join(out_path, 'testplan.json')) as f:
            j = json.load(f)
        filtered_j = [
            (ts['platform'], ts['name'], tc['identifier']) \
               for ts in j['testsuites'] \
               for tc in ts['testcases'] if 'reason' not in tc
        ]

        assert str(sys_exit.value) == '0'

        assert len(filtered_j) == expected_test_count
