const statusMap = {
    '0': 'Tube Initialized in Database',
    '1': 'Patient Assigned',
    '2': 'Sample Returned',
    '3': 'Rack Assigned',
    '4': 'Experiment Initialiated',
    '5': 'Test Completed'
};

export function getStatus(status) {
    return statusMap[status]
}

const reportMap = {
    '-3': 'Not Yet Tested',
    '-2': 'Invalid',
    '-1': 'Inconclusive',
    '0': 'Not Detected',
    '1': 'Positive 2019-nCoV'
};

export function getReport(report) {
    return reportMap[report]
}