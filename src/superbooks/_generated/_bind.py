"""Generated from sdk-manifest.json by scripts/codegen.py. Do not edit.

Run ``python scripts/codegen.py`` to regenerate.
"""

from __future__ import annotations

from .._transport import AsyncTransport, SyncTransport
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

__all__ = ["AsyncNamespaces", "SyncNamespaces"]


class SyncNamespaces:
    """Typed tool namespaces attached to the sync client."""

    transactions: Transactions
    invoices: Invoices
    customers: Customers
    categories: Categories
    tags: Tags
    documents: Documents
    inbox: Inbox
    tracker: Tracker
    bank_accounts: BankAccounts
    team: Team
    search: Search
    reports: Reports

    def _bind_namespaces(self, transport: SyncTransport) -> None:
        self.transactions = Transactions(transport)
        self.invoices = Invoices(transport)
        self.customers = Customers(transport)
        self.categories = Categories(transport)
        self.tags = Tags(transport)
        self.documents = Documents(transport)
        self.inbox = Inbox(transport)
        self.tracker = Tracker(transport)
        self.bank_accounts = BankAccounts(transport)
        self.team = Team(transport)
        self.search = Search(transport)
        self.reports = Reports(transport)


class AsyncNamespaces:
    """Typed tool namespaces attached to the async client."""

    transactions: AsyncTransactions
    invoices: AsyncInvoices
    customers: AsyncCustomers
    categories: AsyncCategories
    tags: AsyncTags
    documents: AsyncDocuments
    inbox: AsyncInbox
    tracker: AsyncTracker
    bank_accounts: AsyncBankAccounts
    team: AsyncTeam
    search: AsyncSearch
    reports: AsyncReports

    def _bind_namespaces(self, transport: AsyncTransport) -> None:
        self.transactions = AsyncTransactions(transport)
        self.invoices = AsyncInvoices(transport)
        self.customers = AsyncCustomers(transport)
        self.categories = AsyncCategories(transport)
        self.tags = AsyncTags(transport)
        self.documents = AsyncDocuments(transport)
        self.inbox = AsyncInbox(transport)
        self.tracker = AsyncTracker(transport)
        self.bank_accounts = AsyncBankAccounts(transport)
        self.team = AsyncTeam(transport)
        self.search = AsyncSearch(transport)
        self.reports = AsyncReports(transport)
