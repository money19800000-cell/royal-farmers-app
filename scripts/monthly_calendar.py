"""Keep calendar gaps visible without inventing player statistics."""
import re


def calendar_month_keys(sourceMonths, asOf):
    endMonth = asOf[:6]
    def monthIndex(month):
        if not re.fullmatch(r'\d{4}(0[1-9]|1[0-2])', month):
            raise ValueError(f'Invalid month: {month}')
        return int(month[:4]) * 12 + int(month[4:]) - 1
    endIndex = monthIndex(endMonth)
    observed = [monthIndex(month) for month in sourceMonths]
    startIndex = min([index for index in observed if index <= endIndex] or [endIndex])
    return [f'{index // 12:04d}{index % 12 + 1:02d}'
            for index in range(endIndex, startIndex - 1, -1)]
