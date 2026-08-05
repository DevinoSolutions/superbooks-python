"""Generated from sdk-manifest.json by scripts/codegen.py. Do not edit.

Run ``python scripts/codegen.py`` to regenerate.
"""

from __future__ import annotations

from ._async import (
    AsyncBankAccounts,
    AsyncCategories,
    AsyncCustomers,
    AsyncDocuments,
    AsyncInbox,
    AsyncInvoices,
    AsyncReports,
    AsyncSearch,
    AsyncTags,
    AsyncTeam,
    AsyncTracker,
    AsyncTransactions,
)
from ._sync import (
    BankAccounts,
    Categories,
    Customers,
    Documents,
    Inbox,
    Invoices,
    Reports,
    Search,
    Tags,
    Team,
    Tracker,
    Transactions,
)

#: Domain name -> (sync namespace class, async namespace class).
DOMAINS: dict[str, tuple[type, type]] = {
    "transactions": (Transactions, AsyncTransactions),
    "invoices": (Invoices, AsyncInvoices),
    "customers": (Customers, AsyncCustomers),
    "categories": (Categories, AsyncCategories),
    "tags": (Tags, AsyncTags),
    "documents": (Documents, AsyncDocuments),
    "inbox": (Inbox, AsyncInbox),
    "tracker": (Tracker, AsyncTracker),
    "bank_accounts": (BankAccounts, AsyncBankAccounts),
    "team": (Team, AsyncTeam),
    "search": (Search, AsyncSearch),
    "reports": (Reports, AsyncReports),
}

TOOL_COUNT = 45

__all__ = [
    "DOMAINS",
    "TOOL_COUNT",
    "AsyncBankAccounts",
    "AsyncCategories",
    "AsyncCustomers",
    "AsyncDocuments",
    "AsyncInbox",
    "AsyncInvoices",
    "AsyncReports",
    "AsyncSearch",
    "AsyncTags",
    "AsyncTeam",
    "AsyncTracker",
    "AsyncTransactions",
    "BankAccounts",
    "Categories",
    "Customers",
    "Documents",
    "Inbox",
    "Invoices",
    "Reports",
    "Search",
    "Tags",
    "Team",
    "Tracker",
    "Transactions",
]
