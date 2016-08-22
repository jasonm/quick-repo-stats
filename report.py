from github3 import login
import datetime
import operator
import pytz
import re

def fetch_prs_merged(date_from, date_to):
    # login
    token = open(".token").read().strip()
    gh = login(token=token)

    # fetch
    repo = gh.repository('minervaproject', 'schools')
    recent_prs = list(repo.pull_requests(state='closed', number=100))

    def include_pr(pr):
        return (pr.merged_at is not None) and \
               (date_from < pr.merged_at < date_to) and \
               (pr.title != "Merge development to master")

    prs = filter(include_pr, recent_prs)
    return sorted(prs, key=operator.attrgetter('merged_at'))


def comments_description(pr):
    comments = list(pr.issue_comments()) + list(pr.review_comments())
    users = set([comment.user.login for comment in comments])
    if len(comments) == 0:
        return "0"
    return "{} by {} users".format(len(comments), len(users))


def test_overview(pr):
    def is_test_file(f):
        return re.search(r"test.*test_.*py", f.filename) is not None

    files = list(pr.files())
    test_files = filter(is_test_file, files)

    if len(test_files) == 0:
        return "No tests"

    test_additions = sum([f.additions_count for f in test_files])
    test_changes = sum([f.changes_count for f in test_files])
    test_deletions = sum([f.deletions_count for f in test_files])

    return "{}+/{}-/{} changed".format(test_additions, test_deletions, test_changes)


# report
def print_report_tsv(date_from, date_to):
    print "Username\tMerged\tTitle\tNumber\tLink\tComments\tTests"
    for pr in fetch_prs_merged(date_from, date_to):
        print "{username}\t{merged}\t{title}\t{number}\t{link}\t{comments}\t{test_overview}".format(
            username=pr.user.login,
            merged=pr.merged_at.strftime("%a %Y-%m-%d"),
            title=pr.title,
            number=pr.number,
            link=pr.html_url,
            comments=comments_description(pr),
            test_overview=test_overview(pr),
        )


# interactive prompt
tz_pacific = pytz.timezone('US/Pacific')
def prompt_date(label, default):
    date_string = raw_input("{} [{}]:".format(label, default)) or default
    return tz_pacific.localize(datetime.datetime.strptime(date_string, "%Y-%m-%d"))


# http://stackoverflow.com/questions/6172782/find-the-friday-of-previous-last-week-in-python
def most_recent_monday():
    return datetime.datetime.now() - datetime.timedelta(days=datetime.datetime.now().weekday())


if __name__ == '__main__':
    date_from = prompt_date("Date from (inclusive)", most_recent_monday().strftime("%Y-%m-%d"))
    date_to = prompt_date("Date to (exclusive)", (most_recent_monday() + datetime.timedelta(weeks=1)).strftime("%Y-%m-%d"))
    print_report_tsv(date_from, date_to)
