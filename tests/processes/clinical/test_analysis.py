from flaskr.clinical_data.view_model.runprocessor import RunProcessor


def test_targets():
    # TODO: confirm that n1, n2, rp show up for each sample
    assert True


def test_positive_controls():
    processor = RunProcessor()
    test_line = [['nan', 'A01', 'FAM', 'N1', 'Unkn', 'PC', 'nan', 25, 25, 0, 'nan', 'nan', 'nan', 0, 55, 'nan'],
                 ['nan', 'A01', 'FAM', 'N2', 'Unkn', 'PC', 'nan', 25, 25, 0, 'nan', 'nan', 'nan', 0, 55, 'nan'],
                 ['nan', 'A01', 'FAM', 'RP', 'Unkn', 'PC', 'nan', 0, 0, 0, 'nan', 'nan', 'nan', 0, 55, 'nan']]
    for idx, line in enumerate(test_line):
        pc_result = processor.execute(line, idx)
        if idx == 2:
            assert not pc_result.is_success()
        else:
            assert pc_result.is_success()


def test_negative_controls():
    processor = RunProcessor()
    test_line = [['nan', 'A01', 'FAM', 'N1', 'Unkn', 'NFW', 'nan', 25, 25, 0, 'nan', 'nan', 'nan', 0, 55, 'nan'],
                 ['nan', 'A01', 'FAM', 'N2', 'Unkn', 'NFW', 'nan', 0, 25, 0, 'nan', 'nan', 'nan', 0, 55, 'nan'],
                 ['nan', 'A01', 'FAM', 'RP', 'Unkn', 'NFW', 'nan', 0, 0, 0, 'nan', 'nan', 'nan', 0, 55, 'nan']]

    for idx, line in enumerate(test_line):
        nfw_fail = processor.execute(line, idx)
    assert not nfw_fail.is_success()

    test_line[0][7] = 0
    for idx, line in enumerate(test_line):
        nfw_pass = processor.execute(line, idx)
    assert nfw_pass.is_success()


def test_inconclusive():
    processor = RunProcessor()
    test_line = [['nan', 'A01', 'FAM', 'N1', 'Unkn', 'A0000', 'nan', 25, 25, 0, 'nan', 'nan', 'nan', 0, 55, 'nan'],
                 ['nan', 'A01', 'FAM', 'N2', 'Unkn', 'A0000', 'nan', 0, 25, 0, 'nan', 'nan', 'nan', 0, 55, 'nan'],
                 ['nan', 'A01', 'FAM', 'RP', 'Unkn', 'A0000', 'nan', 0, 0, 0, 'nan', 'nan', 'nan', 0, 55, 'nan']]
    for idx, line in enumerate(test_line):
        inconclusive = processor.execute(line, idx)
    assert processor.results[test_line[0][5]]['Report'] == -1


def test_invalid():
    processor = RunProcessor()
    test_line = [['nan', 'A01', 'FAM', 'N1', 'Unkn', 'A0000', 'nan', 0, 25, 0, 'nan', 'nan', 'nan', 0, 55, 'nan'],
                 ['nan', 'A01', 'FAM', 'N2', 'Unkn', 'A0000', 'nan', 0, 25, 0, 'nan', 'nan', 'nan', 0, 55, 'nan'],
                 ['nan', 'A01', 'FAM', 'RP', 'Unkn', 'A0000', 'nan', 0, 0, 0, 'nan', 'nan', 'nan', 0, 55, 'nan']]
    for idx, line in enumerate(test_line):
        invalid = processor.execute(line, idx)
    assert processor.results[test_line[0][5]]['Report'] == -2


def test_not_detected():
    processor = RunProcessor()
    test_line = [['nan', 'A01', 'FAM', 'N1', 'Unkn', 'A0000', 'nan', 0, 25, 0, 'nan', 'nan', 'nan', 0, 55, 'nan'],
                 ['nan', 'A01', 'FAM', 'N2', 'Unkn', 'A0000', 'nan', 0, 25, 0, 'nan', 'nan', 'nan', 0, 55, 'nan'],
                 ['nan', 'A01', 'FAM', 'RP', 'Unkn', 'A0000', 'nan', 27, 0, 0, 'nan', 'nan', 'nan', 0, 55, 'nan']]
    for idx, line in enumerate(test_line):
        not_detected = processor.execute(line, idx)
    assert processor.results[test_line[0][5]]['Report'] == 0


def test_detected():
    processor = RunProcessor()
    test_line = [['nan', 'A01', 'FAM', 'N1', 'Unkn', 'A0000', 'nan', 25, 25, 0, 'nan', 'nan', 'nan', 0, 55, 'nan'],
                 ['nan', 'A01', 'FAM', 'N2', 'Unkn', 'A0000', 'nan', 25, 25, 0, 'nan', 'nan', 'nan', 0, 55, 'nan'],
                 ['nan', 'A01', 'FAM', 'RP', 'Unkn', 'A0000', 'nan', 27, 0, 0, 'nan', 'nan', 'nan', 0, 55, 'nan']]
    for idx, line in enumerate(test_line):
        not_detected = processor.execute(line, idx)
    assert processor.results[test_line[0][5]]['Report'] == 1
