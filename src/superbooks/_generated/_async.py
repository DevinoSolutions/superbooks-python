"""Generated from sdk-manifest.json by scripts/codegen.py. Do not edit.

Run ``python scripts/codegen.py`` to regenerate.
"""

from __future__ import annotations

import builtins
from typing import Any, Literal

from .._namespace import AsyncNamespace

__all__ = [
    'AsyncBankAccounts',
    'AsyncCategories',
    'AsyncCustomers',
    'AsyncDocuments',
    'AsyncInbox',
    'AsyncInvoices',
    'AsyncReports',
    'AsyncSearch',
    'AsyncTags',
    'AsyncTeam',
    'AsyncTracker',
    'AsyncTransactions',
]

class AsyncTransactions(AsyncNamespace):
    """`transactions` tools (5 available)."""

    async def list(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        status: Literal["posted", "pending", "excluded", "completed", "archived", "exported"] | None = None,
        category_slug: str | None = None,
        bank_account_id: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> Any:
        """
        List bank transactions for the current team, newest first. Supports cursor
        pagination plus filters by date range, status, category slug, and bank
        account. Pass the returned nextCursor to fetch the next page.

        Args:
            from_: Inclusive lower bound, YYYY-MM-DD.
            to: Inclusive upper bound, YYYY-MM-DD.
            status: Filter by workflow status.
            category_slug: Filter by category slug.
            bank_account_id: Filter by bank account ID.
            cursor: Pagination cursor returned by the previous call.
            limit: Max items per page (1-100). Defaults to 25 server-side.
        """
        return await self._call(
            "transactions_list",
            {
                "from": from_,
                "to": to,
                "status": status,
                "category_slug": category_slug,
                "bank_account_id": bank_account_id,
                "cursor": cursor,
                "limit": limit,
            },
        )

    async def get(
        self,
        id: str,
    ) -> Any:
        """
        Fetch one transaction by ID with full details (counterparty, attachments,
        notes).

        Args:
            id: Transaction ID.
        """
        return await self._call(
            "transactions_get",
            {
                "id": id,
            },
        )

    async def update_status(
        self,
        id: str,
        status: Literal["posted", "pending", "excluded", "completed", "archived", "exported"],
    ) -> Any:
        """
        Update the workflow status of one transaction (posted | pending | excluded |
        completed | archived | exported). Use 'archived' or 'excluded' for non-
        destructive removal — DO NOT use transactions_delete unless the user
        explicitly asks for permanent deletion.

        Args:
            id: Transaction ID.
            status: New status to assign.
        """
        return await self._call(
            "transactions_update_status",
            {
                "id": id,
                "status": status,
            },
        )

    async def update_category(
        self,
        id: str,
        category_slug: str,
    ) -> Any:
        """
        Assign a category slug to a transaction. The slug must already exist in the
        team's categories table — call categories_list first if you're unsure of
        valid slugs.

        Args:
            id: Transaction ID.
            category_slug: Category slug — must exist in this team's categories.
        """
        return await self._call(
            "transactions_update_category",
            {
                "id": id,
                "category_slug": category_slug,
            },
        )

    async def delete(
        self,
        id: str,
    ) -> Any:
        """
        Permanently delete a transaction. Destructive — confirm with the user before
        calling. Use update_status to 'archived' or 'excluded' for non-destructive
        removal. Returns deleted: false if the transaction was already absent — does
        not throw.

        Destructive. Two gates must both be open: the credential needs the full-
        access `apis.all` scope, and the team must have destructive AI tools
        enabled. Otherwise this raises AuthorizationError.

        Args:
            id: Transaction ID. This action is permanent.
        """
        return await self._call(
            "transactions_delete",
            {
                "id": id,
            },
        )

class AsyncInvoices(AsyncNamespace):
    """`invoices` tools (5 available)."""

    async def list(
        self,
        *,
        status: Literal["draft", "overdue", "paid", "unpaid", "canceled", "scheduled", "refunded"] | None = None,
        from_: str | None = None,
        to: str | None = None,
        customer_id: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> Any:
        """
        List invoices for the current team, ordered by created_at desc (newest
        first). Supports cursor pagination plus filters by status, date range
        (issue_date), and customer. Pass the returned nextCursor to fetch the next
        page.

        Args:
            status: Filter by invoice status.
            from_: Inclusive lower bound on issue_date, YYYY-MM-DD.
            to: Inclusive upper bound on issue_date, YYYY-MM-DD.
            customer_id: Filter by customer ID.
            cursor: Pagination cursor returned by the previous call.
            limit: Max items per page (1-100). Defaults to 25 server-side.
        """
        return await self._call(
            "invoices_list",
            {
                "status": status,
                "from": from_,
                "to": to,
                "customer_id": customer_id,
                "cursor": cursor,
                "limit": limit,
            },
        )

    async def get(
        self,
        id: str,
    ) -> Any:
        """
        Fetch one invoice with line items, customer, and totals.

        Args:
            id: Invoice ID.
        """
        return await self._call(
            "invoices_get",
            {
                "id": id,
            },
        )

    async def create_draft(
        self,
        customer_id: str,
        currency: str,
        issue_date: str,
        due_date: str,
        line_items: builtins.list[builtins.dict[str, Any]],
        *,
        note: str | None = None,
    ) -> Any:
        """
        Create a draft invoice. Draft is not sent to the customer; user reviews and
        calls invoices_send to deliver.

        Args:
            customer_id: Customer ID — must already exist for this team.
            currency: 3-letter currency code (e.g., USD, EUR).
            issue_date: Issue date, YYYY-MM-DD.
            due_date: Due date, YYYY-MM-DD.
            line_items: At least one line item; amount is computed from these.
            note: Optional note shown on the invoice.
        """
        return await self._call(
            "invoices_create_draft",
            {
                "customer_id": customer_id,
                "currency": currency,
                "issue_date": issue_date,
                "due_date": due_date,
                "line_items": line_items,
                "note": note,
            },
        )

    async def send(
        self,
        id: str,
    ) -> Any:
        """
        Mark a draft invoice as sent (status transitions draft -> unpaid; the schema
        does not have a 'sent' status). Triggers customer email delivery in the
        background. Throws if the invoice is not in 'draft' status.

        Args:
            id: Invoice ID to send.
        """
        return await self._call(
            "invoices_send",
            {
                "id": id,
            },
        )

    async def void(
        self,
        id: str,
    ) -> Any:
        """
        Void an invoice (soft-cancel that preserves audit trail). Status becomes
        'canceled' (the schema does not have a 'voided' status; canceled is the
        closest soft-cancel). Destructive — confirm with the user before calling.
        Throws if the invoice is not found OR is already canceled (so re-voiding
        never silently succeeds).

        Destructive. Two gates must both be open: the credential needs the full-
        access `apis.all` scope, and the team must have destructive AI tools
        enabled. Otherwise this raises AuthorizationError.

        Args:
            id: Invoice ID to void.
        """
        return await self._call(
            "invoices_void",
            {
                "id": id,
            },
        )

class AsyncCustomers(AsyncNamespace):
    """`customers` tools (5 available)."""

    async def list(
        self,
        *,
        name: str | None = None,
        email: str | None = None,
        tag_id: str | None = None,
        is_archived: bool | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> Any:
        """
        List customers for the current team, newest first. Supports cursor
        pagination plus filters by name (partial, case-insensitive), email (partial,
        case-insensitive), tag id, and archived state. Pass the returned nextCursor
        to fetch the next page.

        Args:
            name: Partial, case-insensitive match against the customer name.
            email: Partial, case-insensitive match against the customer email.
            tag_id: Only return customers linked to this tag id. Use tags_list to
                find tag ids.
            is_archived: If true, only archived customers. If false, only non-
                archived (default behavior shows all).
            cursor: Pagination cursor returned by the previous call.
            limit: Max items per page (1-100). Defaults to 25 server-side.
        """
        return await self._call(
            "customers_list",
            {
                "name": name,
                "email": email,
                "tag_id": tag_id,
                "is_archived": is_archived,
                "cursor": cursor,
                "limit": limit,
            },
        )

    async def get(
        self,
        id: str,
    ) -> Any:
        """
        Fetch one customer by ID with full billing/shipping details, tags, and
        invoice/project counts. Returns null if not found for the current team.

        Args:
            id: Customer ID.
        """
        return await self._call(
            "customers_get",
            {
                "id": id,
            },
        )

    async def create(
        self,
        name: str,
        email: str,
        *,
        billingEmail: Any | None = None,
        phone: Any | None = None,
        website: Any | None = None,
        contact: Any | None = None,
        note: Any | None = None,
        vatNumber: Any | None = None,
        country: Any | None = None,
        countryCode: Any | None = None,
        addressLine1: Any | None = None,
        addressLine2: Any | None = None,
        city: Any | None = None,
        state: Any | None = None,
        zip: Any | None = None,
        preferred_currency: Any | None = None,
        default_payment_terms: Any | None = None,
        tag_ids: builtins.list[str] | None = None,
    ) -> Any:
        """
        Create a new customer for the current team. Name and email are required;
        billing/shipping address fields and tags are optional. To assign tags, pass
        an array of existing tag ids (use tags_list/tags_create from the tags domain
        to manage them — this tool does NOT create new tags).

        Args:
            name: Customer or organization name (e.g., 'Acme Corporation').
            email: Primary email address of the customer.
            billingEmail: Billing email address(es). Comma-separate multiple values
                (e.g., 'finance@acme.com, ap@acme.com').
            phone: Primary phone number.
            website: Website URL (e.g., 'https://acme.com').
            contact: Primary contact person's name at the customer organization.
            note: Internal team-facing note about this customer.
            vatNumber: VAT (Value Added Tax) number.
            country: Country name (e.g., 'United States').
            countryCode: Country code in ISO 3166-1 alpha-2 format (e.g., 'US').
            addressLine1: First line of the customer's address.
            addressLine2: Second line of the customer's address (suite, apartment,
                etc.).
            city: City.
            state: State or province.
            zip: ZIP or postal code.
            preferred_currency: 3-letter ISO currency code used as default for new
                invoices (e.g., 'USD'). Will be uppercased.
            default_payment_terms: Default payment terms in days used when
                generating invoices (e.g., 30 for net-30).
            tag_ids: Array of existing tag ids to link to this customer. Tags must
                already exist for the team.
        """
        return await self._call(
            "customers_create",
            {
                "name": name,
                "email": email,
                "billingEmail": billingEmail,
                "phone": phone,
                "website": website,
                "contact": contact,
                "note": note,
                "vatNumber": vatNumber,
                "country": country,
                "countryCode": countryCode,
                "addressLine1": addressLine1,
                "addressLine2": addressLine2,
                "city": city,
                "state": state,
                "zip": zip,
                "preferred_currency": preferred_currency,
                "default_payment_terms": default_payment_terms,
                "tag_ids": tag_ids,
            },
        )

    async def update(
        self,
        id: str,
        *,
        name: str | None = None,
        email: str | None = None,
        billingEmail: Any | None = None,
        phone: Any | None = None,
        website: Any | None = None,
        contact: Any | None = None,
        note: Any | None = None,
        vatNumber: Any | None = None,
        country: Any | None = None,
        countryCode: Any | None = None,
        addressLine1: Any | None = None,
        addressLine2: Any | None = None,
        city: Any | None = None,
        state: Any | None = None,
        zip: Any | None = None,
        preferred_currency: Any | None = None,
        default_payment_terms: Any | None = None,
        is_archived: bool | None = None,
        tag_ids: builtins.list[str] | None = None,
    ) -> Any:
        """
        Update one customer. Only the fields you pass are modified — other fields
        are left untouched. Set is_archived=true to archive (recommended over
        customers_delete for soft removal). If tag_ids is provided, it FULLY
        REPLACES the existing tag set: tags not in the array are unlinked. Omit
        tag_ids entirely to leave tags untouched.

        Args:
            id: Customer ID to update.
            name: New customer name.
            email: New primary email.
            billingEmail: Billing email(s). Pass null to clear. Comma-separate for
                multiple.
            phone: Phone number. Pass null to clear.
            website: Website URL. Pass null to clear.
            contact: Primary contact name. Pass null to clear.
            note: Internal team-facing note. Pass null to clear.
            vatNumber: VAT number. Pass null to clear.
            country: Country name. Pass null to clear.
            countryCode: Country code in ISO 3166-1 alpha-2 format. Pass null to
                clear.
            addressLine1: Address line 1. Pass null to clear.
            addressLine2: Address line 2. Pass null to clear.
            city: City. Pass null to clear.
            state: State or province. Pass null to clear.
            zip: ZIP/postal code. Pass null to clear.
            preferred_currency: 3-letter ISO currency code (uppercased). Pass null
                to clear.
            default_payment_terms: Default payment terms in days for new invoices.
                Pass null to clear.
            is_archived: Archive (true) or restore (false) the customer. Archived
                customers are hidden from default lists.
            tag_ids: REPLACES the customer's tag set. Pass [] to clear all tags.
                Omit this field to leave existing tags untouched. Tags must already
                exist for the team.
        """
        return await self._call(
            "customers_update",
            {
                "id": id,
                "name": name,
                "email": email,
                "billingEmail": billingEmail,
                "phone": phone,
                "website": website,
                "contact": contact,
                "note": note,
                "vatNumber": vatNumber,
                "country": country,
                "countryCode": countryCode,
                "addressLine1": addressLine1,
                "addressLine2": addressLine2,
                "city": city,
                "state": state,
                "zip": zip,
                "preferred_currency": preferred_currency,
                "default_payment_terms": default_payment_terms,
                "is_archived": is_archived,
                "tag_ids": tag_ids,
            },
        )

    async def delete(
        self,
        id: str,
    ) -> Any:
        """
        Permanently delete a customer. DESTRUCTIVE: also permanently deletes all
        tracker projects belonging to this customer, and unlinks the customer from
        invoices and recurring-invoice schedules (those financial records are kept,
        but lose their customer link). Confirm with the user explicitly. Prefer
        customers_update with is_archived=true unless the customer must be removed
        for compliance reasons. Returns deleted: false if the customer was already
        absent — does not throw.

        Destructive. Two gates must both be open: the credential needs the full-
        access `apis.all` scope, and the team must have destructive AI tools
        enabled. Otherwise this raises AuthorizationError.

        Args:
            id: Customer ID. This action is permanent.
        """
        return await self._call(
            "customers_delete",
            {
                "id": id,
            },
        )

class AsyncCategories(AsyncNamespace):
    """`categories` tools (4 available)."""

    async def list(
        self,
    ) -> Any:
        """
        List all transaction categories for the current team. Returns a FLAT array
        (not hierarchical) — each row includes parent_id so the caller can
        reconstruct the parent/child tree if needed. System categories (system:
        true) are included; they cannot be updated or deleted. Ordered by system
        DESC, name ASC. No pagination — the full category catalog is typically
        small.
        """
        return await self._call("categories_list", {})

    async def create(
        self,
        name: str,
        *,
        color: Any | None = None,
        description: Any | None = None,
        parent_id: Any | None = None,
        tax_rate: Any | None = None,
        tax_type: Any | None = None,
        tax_reporting_code: Any | None = None,
        excluded: bool | None = None,
    ) -> Any:
        """
        Create a new transaction category for the current team. Name is required;
        all other fields are optional. The slug is derived from the name (lowercase,
        non-alphanumeric -> underscore, capped at 64 chars). Slugs must be unique
        per team — creating a category with a name that slugifies to an existing
        slug will throw a unique-constraint error. To nest under a parent, pass
        parent_id (the UUID id of an existing category). Returns the created row.

        Args:
            name: Human-readable category name (e.g., 'Office Supplies'). The slug
                is auto-generated from this — pick something stable.
            color: Optional hex color for UI display (e.g., '#FF0000'). Pass null or
                omit if not needed.
            description: Optional free-text description of what this category covers
                (helps the LLM auto-classify transactions).
            parent_id: Optional UUID id of a parent category to nest under. Pass
                null or omit for a top-level category. Use categories_list to find
                existing category ids.
            tax_rate: Optional tax rate as a percentage (e.g., 7.5 for 7.5%). Stored
                with 2-decimal precision.
            tax_type: Optional tax type code (e.g., 'GST', 'VAT', 'sales_tax').
            tax_reporting_code: Optional reporting/jurisdiction code for the tax
                authority's tax line.
            excluded: If true, transactions in this category are excluded from
                financial reports (e.g., transfers between own accounts). Defaults to
                false.
        """
        return await self._call(
            "categories_create",
            {
                "name": name,
                "color": color,
                "description": description,
                "parent_id": parent_id,
                "tax_rate": tax_rate,
                "tax_type": tax_type,
                "tax_reporting_code": tax_reporting_code,
                "excluded": excluded,
            },
        )

    async def update(
        self,
        id: str,
        *,
        name: str | None = None,
        color: Any | None = None,
        description: Any | None = None,
        parent_id: Any | None = None,
        tax_rate: Any | None = None,
        tax_type: Any | None = None,
        tax_reporting_code: Any | None = None,
        excluded: Any | None = None,
    ) -> Any:
        """
        Update one transaction category. Only the fields you pass are modified; omit
        a field to leave it untouched. REFUSES to update a system category (system:
        true). REFUSES to change parent_id on a category that has children — re-nest
        the children first. The slug is NOT updatable (it is part of the composite
        primary key); to rename, create a new category and migrate transactions.
        Returns updated: true on success.

        Args:
            id: Category id (UUID) to update. Use categories_list to find it.
            name: New human-readable name. The slug does NOT change when name
                changes.
            color: Hex color for UI display. Pass null to clear.
            description: Free-text description. Pass null to clear.
            parent_id: Parent category UUID id. Pass null to make top-level. Refused
                if this category already has children.
            tax_rate: Tax rate percentage (e.g., 7.5 for 7.5%). Pass null to clear.
            tax_type: Tax type code (e.g., 'GST', 'VAT'). Pass null to clear.
            tax_reporting_code: Reporting/jurisdiction code. Pass null to clear.
            excluded: If true, this category is excluded from financial reports.
                Pass null to revert to default (false).
        """
        return await self._call(
            "categories_update",
            {
                "id": id,
                "name": name,
                "color": color,
                "description": description,
                "parent_id": parent_id,
                "tax_rate": tax_rate,
                "tax_type": tax_type,
                "tax_reporting_code": tax_reporting_code,
                "excluded": excluded,
            },
        )

    async def delete(
        self,
        id: str,
    ) -> Any:
        """
        Permanently delete a transaction category. DESTRUCTIVE. REFUSES if the
        category is a system category (system: true). REFUSES if any transactions
        still reference the category (by slug) — re-categorize or delete those
        transactions first, then retry. Side-effects on success: any saved
        enrichment rules that reference this category are also deleted. Child
        categories are NOT auto-deleted and will keep pointing at the removed parent
        — re-nest or delete the children first if that matters. Returns deleted:
        false if the category was not found OR was refused; an error is thrown for
        refusals so the caller can distinguish. Confirm with the user before
        calling.

        Destructive. Two gates must both be open: the credential needs the full-
        access `apis.all` scope, and the team must have destructive AI tools
        enabled. Otherwise this raises AuthorizationError.

        Args:
            id: Category id (UUID) to delete. This action is permanent.
        """
        return await self._call(
            "categories_delete",
            {
                "id": id,
            },
        )

class AsyncTags(AsyncNamespace):
    """`tags` tools (3 available)."""

    async def list(
        self,
    ) -> Any:
        """
        List all tags for the current team, ordered by name ascending. Tags are
        simple {id, name} labels that can be attached to customers, transactions,
        and tracker projects via their respective tools. No pagination — the tag
        catalog is typically small.
        """
        return await self._call("tags_list", {})

    async def create(
        self,
        name: str,
    ) -> Any:
        """
        Create a new tag for the current team. Names are unique per team — creating
        a tag whose name already exists throws a clear error (the caller should
        reuse the existing tag id from tags_list). Tags are minimal: only a name is
        stored (no color, no description). Returns {id, name}.

        Args:
            name: Tag name (e.g., 'urgent', 'project-acme'). Must be unique within
                the team.
        """
        return await self._call(
            "tags_create",
            {
                "name": name,
            },
        )

    async def delete(
        self,
        id: str,
    ) -> Any:
        """
        Permanently delete a tag. DESTRUCTIVE: also removes this tag from every
        customer, transaction, and tracker project it is attached to. Those
        customers, transactions, and tracker projects themselves are NOT affected,
        only their tag links. There is no soft-delete/archive for tags. Returns {id,
        deleted: true, name} on success, or {id, deleted: false} if the tag was not
        found for this team. Confirm with the user before calling.

        Destructive. Two gates must both be open: the credential needs the full-
        access `apis.all` scope, and the team must have destructive AI tools
        enabled. Otherwise this raises AuthorizationError.

        Args:
            id: Tag id (UUID) to delete. This action is permanent.
        """
        return await self._call(
            "tags_delete",
            {
                "id": id,
            },
        )

class AsyncDocuments(AsyncNamespace):
    """`documents` tools (4 available)."""

    async def list(
        self,
        *,
        q: Any | None = None,
        tags: Any | None = None,
        start: Any | None = None,
        end: Any | None = None,
        cursor: Any | None = None,
        pageSize: int | None = None,
    ) -> Any:
        """
        List documents (uploaded files in the vault) for the current team, newest
        first. Excludes folder placeholders (`*.folderPlaceholder`). Supports filter
        by tag IDs, date range, and a free-text query `q` (case-insensitive
        substring match on name only). For phrase, fuzzy, or typo-tolerant text
        search, use `documents_search`. Cursor pagination: pass the `cursor` from
        the previous page to get the next one.

        Args:
            q: Case-insensitive substring match on the document name only. For typo-
                tolerant full-text search, use `documents_search` instead.
            tags: Filter to documents that have ANY of these tag IDs.
            start: Inclusive lower bound on the document's `date` (YYYY-MM-DD). Both
                `start` and `end` must be provided together to take effect.
            end: Inclusive upper bound on the document's `date` (YYYY-MM-DD). Both
                `start` and `end` must be provided together to take effect.
            cursor: Pagination cursor from the previous page's `cursor`. Omit on the
                first page.
            pageSize: Number of documents per page (1-100). Defaults to 20. Defaults
                to 20 server-side.
        """
        return await self._call(
            "documents_list",
            {
                "q": q,
                "tags": tags,
                "start": start,
                "end": end,
                "cursor": cursor,
                "pageSize": pageSize,
            },
        )

    async def get(
        self,
        id: str,
    ) -> Any:
        """
        Fetch one document by id with the full row including OCR-extracted text
        (`body`, `content`), title/summary, `tag`, `language`, processing status,
        and assigned tag IDs. Returns null if not found for the current team.

        Args:
            id: Document id (UUID).
        """
        return await self._call(
            "documents_get",
            {
                "id": id,
            },
        )

    async def search(
        self,
        q: str,
        *,
        start: Any | None = None,
        end: Any | None = None,
        tags: Any | None = None,
        cursor: Any | None = None,
        pageSize: int | None = None,
    ) -> Any:
        """
        Full-text search documents by phrase, with substring and typo-tolerant
        matching on the document name. Use this (not `documents_list`) when the user
        asks to find documents by phrase, invoice number, vendor name, etc. — it
        handles typos and partial matches. Returns one page of results newest first
        by `created_at`; pass the returned `cursor` to fetch more.

        Args:
            q: Free-text query — words are matched as prefix terms with English-
                language stemming, plus substring and fuzzy matching on the document
                name to catch near-miss spellings.
            start: Optional inclusive lower bound on the document's `date` (YYYY-MM-
                DD). Both `start` and `end` must be provided together to filter by date.
            end: Optional inclusive upper bound on the document's `date` (YYYY-MM-
                DD). Both `start` and `end` must be provided together to filter by date.
            tags: Optional list of tag IDs — narrows results to documents that have
                ANY of these tags assigned.
            cursor: Pagination cursor from the previous page's `cursor`. Omit on the
                first page.
            pageSize: Number of documents per page (1-100). Defaults to 20. Defaults
                to 20 server-side.
        """
        return await self._call(
            "documents_search",
            {
                "q": q,
                "start": start,
                "end": end,
                "tags": tags,
                "cursor": cursor,
                "pageSize": pageSize,
            },
        )

    async def delete(
        self,
        id: str,
    ) -> Any:
        """
        Permanently delete a document by id. DESTRUCTIVE. Side-effects: (a) all tag
        assignments for this document are removed; (b) any transaction attachments
        that reference this document's stored file are also deleted, so the file
        stops appearing on those transactions; (c) the underlying stored file is
        permanently deleted. Returns `deleted: false` if the document was not found
        for this team — does not throw. Confirm with the user before calling.

        Destructive. Two gates must both be open: the credential needs the full-
        access `apis.all` scope, and the team must have destructive AI tools
        enabled. Otherwise this raises AuthorizationError.

        Args:
            id: Document id (UUID) to delete. This action is permanent.
        """
        return await self._call(
            "documents_delete",
            {
                "id": id,
            },
        )

class AsyncInbox(AsyncNamespace):
    """`inbox` tools (3 available)."""

    async def list(
        self,
        *,
        status: Any | None = None,
        q: Any | None = None,
        cursor: Any | None = None,
        pageSize: int | None = None,
    ) -> Any:
        """
        List inbox items (uploaded receipts / forwarded invoices) for the current
        team, newest first. EXCLUDES soft-deleted items (`status='deleted'`) and
        grouped follow-ups, so each primary item appears once. Filter by exact
        status and/or a free-text query `q` (matches `display_name` / `file_name` /
        `description`; numeric `q` also matches `amount` within +/- 10% tolerance).
        Cursor pagination: pass the `cursor` from the previous page to get the next
        one.

        Args:
            status: Filter by exact inbox_status. Common values: 'pending' (awaiting
                action), 'done' (matched), 'suggested_match' (auto-matched, needs
                confirm), 'no_match' (no candidate transaction). Omit to see everything
                except deleted.
            q: Free-text query — substring-matches `display_name` / `file_name` /
                `description`, case-insensitively. If parseable as a number, ALSO
                matches inbox items with `amount` within +/- 10% of that value.
            cursor: Pagination cursor from the previous page's `cursor`. Omit on the
                first page.
            pageSize: Items per page (1-100). Defaults to 20. Defaults to 20 server-
                side.
        """
        return await self._call(
            "inbox_list",
            {
                "status": status,
                "q": q,
                "cursor": cursor,
                "pageSize": pageSize,
            },
        )

    async def match_(
        self,
        id: str,
        transactionId: str,
    ) -> Any:
        """
        Link an inbox item (receipt / invoice) to a bank transaction. NOT a simple
        flag flip — this: (a) attaches each grouped sibling to the same transaction;
        (b) copies `tax_amount` / `tax_rate+tax_type` from the inbox item onto the
        transaction (only if the inbox has them); (c) sets each linked inbox item's
        `status='done'` and stores its `attachment_id` + `transaction_id`.
        IDEMPOTENT when the item is already matched to the SAME transaction. Throws
        if the item is already matched to a DIFFERENT transaction, if any grouped
        sibling is matched to a different txn, or if the target transaction does not
        exist for this team.

        Args:
            id: Inbox item id (UUID). If this is a grouped follow-up, the entire
                group is matched together.
            transactionId: Target transaction id (UUID). Must belong to the same
                team or the operation throws.
        """
        return await self._call(
            "inbox_match",
            {
                "id": id,
                "transactionId": transactionId,
            },
        )

    async def delete(
        self,
        id: str,
    ) -> Any:
        """
        SOFT-DELETE an inbox item — sets `status='deleted'` and clears its
        `transaction_id` / `attachment_id`; the item itself is retained, not
        removed. DESTRUCTIVE because it irreversibly: (a) detaches the item from its
        linked transaction, deleting that attachment; (b) RESETS the linked
        transaction's `tax_rate` and `tax_type` to NULL if that was its only
        attachment; (c) discards any pending match suggestions for this inbox item.
        The uploaded file itself is retained. Returns `deleted: false` if the inbox
        item was not found for this team — does not throw. Confirm with the user
        before calling.

        Destructive. Two gates must both be open: the credential needs the full-
        access `apis.all` scope, and the team must have destructive AI tools
        enabled. Otherwise this raises AuthorizationError.

        Args:
            id: Inbox item id (UUID) to soft-delete. This action's side-effects on
                linked transactions are irreversible.
        """
        return await self._call(
            "inbox_delete",
            {
                "id": id,
            },
        )

class AsyncTracker(AsyncNamespace):
    """`tracker` tools (5 available)."""

    async def list_projects(
        self,
        *,
        customer_id: Any | None = None,
        status: Any | None = None,
        cursor: Any | None = None,
        limit: int | None = None,
    ) -> Any:
        """
        List tracker projects for the current team, newest first. Use this to
        discover project ids before starting timers or pulling entries. Supports
        filter by customer id and status (`in_progress` / `completed`). Each row
        includes the project's customer (id+name) when set. Cursor pagination: pass
        the `cursor` from the previous page to get the next one.

        Args:
            customer_id: Filter to projects belonging to this customer id. Omit to
                include projects for all customers.
            status: Filter by `trackerStatus`: `in_progress` (active) or
                `completed`. Omit to return both.
            cursor: Pagination cursor from the previous page's `cursor`. Omit on the
                first page.
            limit: Max items per page (1-100). Defaults to 25. Defaults to 25
                server-side.
        """
        return await self._call(
            "tracker_list_projects",
            {
                "customer_id": customer_id,
                "status": status,
                "cursor": cursor,
                "limit": limit,
            },
        )

    async def list_entries(
        self,
        *,
        from_: Any | None = None,
        to: Any | None = None,
        project_id: Any | None = None,
        assigned_id: Any | None = None,
        cursor: Any | None = None,
        limit: int | None = None,
    ) -> Any:
        """
        List tracker time entries for the current team across a date range, newest
        first. Default scope is the CURRENT USER's entries — pass `assigned_id:
        null` to see every teammate. Date range filters the `date` field (the
        timesheet date) — both `from` and `to` must be provided together
        (inclusive). Filter by `project_id` to restrict to one project. `duration`
        is in seconds. Cursor pagination: pass the `cursor` from the previous page
        to get the next one.

        Args:
            from_: Inclusive lower bound on the entry's `date` (YYYY-MM-DD). Both
                `from` and `to` must be provided together to take effect.
            to: Inclusive upper bound on the entry's `date` (YYYY-MM-DD). Both
                `from` and `to` must be provided together to take effect.
            project_id: Filter to entries for this tracker project id. Omit to
                include all projects.
            assigned_id: Filter to entries assigned to this user id. Defaults to the
                CURRENT USER. Pass `null` explicitly to disable the filter and return
                entries from every teammate.
            cursor: Pagination cursor from the previous page's `cursor`. Omit on the
                first page.
            limit: Max items per page (1-100). Defaults to 50. Defaults to 50
                server-side.
        """
        return await self._call(
            "tracker_list_entries",
            {
                "from": from_,
                "to": to,
                "project_id": project_id,
                "assigned_id": assigned_id,
                "cursor": cursor,
                "limit": limit,
            },
        )

    async def start_timer(
        self,
        project_id: str,
        *,
        description: Any | None = None,
        start: Any | None = None,
        assigned_id: Any | None = None,
    ) -> Any:
        """
        Start a tracker timer for the current user on a project. Automatically STOPS
        any timer the user already has running TODAY before creating the new one
        (mirrors the canonical web behavior — only one running timer per user per
        day). `start` defaults to now; `assigned_id` defaults to the current user.
        Returns the newly created entry. Use `tracker_stop_timer` to close it.

        Args:
            project_id: Tracker project id to log time against. Required. Look up
                ids via `tracker_list_projects`.
            description: Free-text description of what's being worked on. Optional —
                can be filled in later via the canonical upsert flow.
            start: ISO 8601 datetime to use as the start moment. Defaults to NOW.
                Use this only when backfilling a timer that started slightly earlier.
            assigned_id: User id to assign the timer to. Defaults to the current
                user. Only set when logging time on behalf of a teammate.
        """
        return await self._call(
            "tracker_start_timer",
            {
                "project_id": project_id,
                "description": description,
                "start": start,
                "assigned_id": assigned_id,
            },
        )

    async def stop_timer(
        self,
        *,
        entry_id: Any | None = None,
        stop: Any | None = None,
        assigned_id: Any | None = None,
    ) -> Any:
        """
        Stop the current user's running tracker timer (or a specific entry by id).
        If duration is under 60 seconds, the entry is DELETED as an accidental tap —
        the response sets `discarded: true`. Otherwise the entry is updated with
        `stop` and `duration` (seconds). `entry_id` is optional — when omitted,
        finds the user's running timer for TODAY. Throws if no running timer exists,
        the entry is already stopped, or the entry has no `start`.

        Args:
            entry_id: Specific tracker entry id to stop. Omit to auto-stop the
                current user's running timer for today.
            stop: ISO 8601 datetime to use as the stop moment. Defaults to NOW. Set
                when correcting a timer's stop time.
            assigned_id: User id whose timer to stop. Defaults to the current user.
                Only set when stopping a teammate's timer.
        """
        return await self._call(
            "tracker_stop_timer",
            {
                "entry_id": entry_id,
                "stop": stop,
                "assigned_id": assigned_id,
            },
        )

    async def delete_entry(
        self,
        id: str,
    ) -> Any:
        """
        Permanently delete a tracker time entry. DESTRUCTIVE — confirm with the user
        before calling. Deleting an entry has no knock-on effects — the projects,
        customers, and invoices it relates to are left untouched. Returns deleted:
        false if the entry was already absent — does not throw.

        Destructive. Two gates must both be open: the credential needs the full-
        access `apis.all` scope, and the team must have destructive AI tools
        enabled. Otherwise this raises AuthorizationError.

        Args:
            id: Tracker entry id (UUID). This action is permanent.
        """
        return await self._call(
            "tracker_delete_entry",
            {
                "id": id,
            },
        )

class AsyncBankAccounts(AsyncNamespace):
    """`bank_accounts` tools (1 available)."""

    async def list(
        self,
        *,
        enabled: Any | None = None,
        manual: Any | None = None,
    ) -> Any:
        """
        List bank accounts for the current team with the connected institution's
        name + logo when available. Use this to discover bank account ids before
        listing transactions, attaching payment info to an invoice, etc. Supports
        filter by `enabled` (active accounts only) and `manual` (user-created vs.
        provider-synced). Does NOT decrypt IBAN / account numbers — those require a
        separate explicit reveal action.

        Args:
            enabled: Filter by enabled state. `true` returns only active accounts;
                `false` returns disabled ones. Omit to include both.
            manual: Filter by source. `true` returns only manually created accounts;
                `false` returns only provider-synced
                (Plaid/GoCardless/Teller/EnableBanking) accounts. Omit to include both.
        """
        return await self._call(
            "bank_accounts_list",
            {
                "enabled": enabled,
                "manual": manual,
            },
        )

class AsyncTeam(AsyncNamespace):
    """`team` tools (1 available)."""

    async def get(
        self,
    ) -> Any:
        """
        Get the current team's metadata: name, logo, base currency, country, fiscal
        year start, subscription plan + status, inbox id/email, and Stripe Connect
        status. The team is implicit (resolved from the authenticated request
        context) — no arguments. Returns null if the team has been deleted
        underneath the session.
        """
        return await self._call("team_get", {})

class AsyncSearch(AsyncNamespace):
    """`search` tools (1 available)."""

    async def global_(
        self,
        query: str,
        *,
        limit: int | None = None,
        per_table_limit: int | None = None,
        relevance_threshold: float | None = None,
    ) -> Any:
        """
        Cross-entity full-text search over transactions, invoices, customers,
        documents, and inbox items for the current team. Tokenizes the free-text
        query into prefix terms combined with AND (`foo bar` matches records
        containing a word starting with `foo` AND a word starting with `bar`) and
        ranks results by relevance. Use when the user asks an open-ended 'find
        anything mentioning X' question; for entity-specific search prefer the per-
        domain tools (`documents_search`, etc.). Returns an array of `{ id, type,
        relevance, created_at, data }` rows — `data` carries entity-specific fields
        for rendering without an extra fetch.

        Args:
            query: Free-text query. Words are matched as prefix terms combined with
                AND, using English-language stemming.
            limit: Maximum total results across all entity types (1-100). Defaults
                to 30. Defaults to 30 server-side.
            per_table_limit: Maximum matches per entity type before results are
                merged and ranked (1-50). Defaults to 10. Defaults to 10 server-side.
            relevance_threshold: Minimum relevance score (0-1) for a row to be
                returned. Defaults to 0.01. Defaults to 0.01 server-side.
        """
        return await self._call(
            "search_global",
            {
                "query": query,
                "limit": limit,
                "per_table_limit": per_table_limit,
                "relevance_threshold": relevance_threshold,
            },
        )

class AsyncReports(AsyncNamespace):
    """`reports` tools (8 available)."""

    async def burn_rate(
        self,
        from_: str,
        to: str,
    ) -> Any:
        """
        Monthly burn (total expenses) for the current team over a date range,
        expressed in the team's base currency. Each row reports a `YYYY-MM` month
        label, the absolute sum of negative-amount transactions in that month, and
        the base currency code. Also returns the simple arithmetic mean across the
        returned months (`average`). Cross-currency transactions are excluded so the
        monthly series is apples-to-apples. Use this when the user asks 'what's my
        burn', 'how much did I spend per month', or wants a trend chart of expenses.

        Args:
            from_: Inclusive lower bound on transaction `date` (YYYY-MM-DD). Months
                are bucketed at calendar boundaries — partial months are included with
                whatever transactions fall in the window.
            to: Inclusive upper bound on transaction `date` (YYYY-MM-DD).
        """
        return await self._call(
            "reports_burn_rate",
            {
                "from": from_,
                "to": to,
            },
        )

    async def runway(
        self,
    ) -> Any:
        """
        Months of runway based on current cash position and average monthly burn
        over the last 6 calendar months — all expressed in the team's base currency.
        Returns `{ months, cash, avg_burn, currency }`. `months` is `null` (not
        Infinity) when `avg_burn` is zero, so downstream JSON renders are safe.
        Cross-currency cash AND cross-currency expenses are EXCLUDED to keep the
        ratio coherent. Use when the user asks 'how long can we last', 'what's my
        runway', or any survival-time question. For per-currency cash positions use
        `reports_balance`; for the monthly burn series itself use
        `reports_burn_rate`.
        """
        return await self._call("reports_runway", {})

    async def profit_loss(
        self,
        from_: str,
        to: str,
    ) -> Any:
        """
        Monthly profit & loss for the current team over a date range — revenue
        (positive transactions), expense (absolute value of negative transactions),
        and delta (revenue - expense) per `YYYY-MM` month. Also returns aggregate
        totals across the range. All values are in the team's base currency; cross-
        currency transactions are excluded. Use when the user asks 'show my P&L',
        'am I profitable', or wants a profit/expense breakdown by month.

        Args:
            from_: Inclusive lower bound on transaction `date` (YYYY-MM-DD). Months
                are bucketed at calendar boundaries.
            to: Inclusive upper bound on transaction `date` (YYYY-MM-DD).
        """
        return await self._call(
            "reports_profit_loss",
            {
                "from": from_,
                "to": to,
            },
        )

    async def revenue(
        self,
        from_: str,
        to: str,
    ) -> Any:
        """
        Monthly revenue for the current team over a date range — the sum of
        POSITIVE-amount transactions per `YYYY-MM` month, in the team's base
        currency. Also returns the grand total. Cross-currency transactions are
        excluded. This is cash-in revenue (the bank-ledger view); for invoiced
        revenue by customer use `reports_top_customers` instead. Use when the user
        asks 'show revenue', 'how much did I make', or wants a revenue trend chart.

        Args:
            from_: Inclusive lower bound on transaction `date` (YYYY-MM-DD).
            to: Inclusive upper bound on transaction `date` (YYYY-MM-DD).
        """
        return await self._call(
            "reports_revenue",
            {
                "from": from_,
                "to": to,
            },
        )

    async def spending(
        self,
        from_: str,
        to: str,
    ) -> Any:
        """
        Spending grouped by transaction category for the current team over a date
        range. Sums absolute value of negative-amount transactions per
        `category_slug` in the team's base currency, sorted by amount descending.
        Uncategorized transactions are EXCLUDED from both the breakdown and the
        `total` (so the total matches the sum of the array). Cross-currency
        transactions are excluded. Use when the user asks 'where is my money going',
        'spending by category', or wants a category-level expense breakdown. For a
        time-series view use `reports_burn_rate`.

        Args:
            from_: Inclusive lower bound on transaction `date` (YYYY-MM-DD).
            to: Inclusive upper bound on transaction `date` (YYYY-MM-DD).
        """
        return await self._call(
            "reports_spending",
            {
                "from": from_,
                "to": to,
            },
        )

    async def balance(
        self,
    ) -> Any:
        """
        Sum of bank account balances grouped by currency for the current team.
        Returns one entry per distinct currency among ENABLED accounts (disabled /
        connection-paused accounts are excluded). Each entry's `amount` is the raw
        stored balance — no FX conversion is applied, so callers should not naively
        add across currencies. Use this when the user asks 'how much cash do I
        have', 'show my balances', or anything cash-position related. For a single-
        number runway calculation in the team's base currency, use `reports_runway`
        instead.
        """
        return await self._call("reports_balance", {})

    async def top_customers(
        self,
        *,
        from_: Any | None = None,
        to: Any | None = None,
        limit: int | None = None,
    ) -> Any:
        """
        Top customers by paid invoice revenue for the current team, sorted
        descending. Groups by `(customer_id, currency)` so a customer billed in two
        currencies appears as two rows — currencies are kept separate to avoid
        silent FX mixing. Only `status = 'paid'` invoices contribute. Date range
        filters on `paid_at` (cash receipt date); omit both `from` and `to` for all-
        time totals. `customer_name` is denormalized from the customers table; if
        the invoice references a deleted customer the name will be null. Use when
        the user asks 'who are my best customers', 'top revenue contributors', or
        'biggest accounts'.

        Args:
            from_: Inclusive lower bound on invoice `paid_at` (YYYY-MM-DD). Omit to
                disable the lower bound.
            to: Inclusive upper bound on invoice `paid_at` (YYYY-MM-DD). Omit to
                disable the upper bound.
            limit: Maximum number of (customer, currency) rows to return (1-100).
                Defaults to 10. Defaults to 10 server-side.
        """
        return await self._call(
            "reports_top_customers",
            {
                "from": from_,
                "to": to,
                "limit": limit,
            },
        )

    async def recurring_expenses(
        self,
    ) -> Any:
        """
        Heuristically detected recurring expenses for the current team. A
        counterparty (vendor) is flagged when it appears in at least 3 of the last 6
        calendar months with negative-amount transactions in the team's base
        currency. Returns `{ counterparty, months, avg_amount, currency }` per
        match, sorted by `months` desc then `avg_amount` desc. `months` is the count
        of distinct months the counterparty appeared in (max 6). NULL counterparties
        are skipped. Use when the user asks 'what subscriptions am I paying for',
        'recurring bills', or wants to audit ongoing vendor spend.
        """
        return await self._call("reports_recurring_expenses", {})
