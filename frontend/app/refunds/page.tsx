import type { Metadata } from "next";
import Link from "next/link";
import { Callout, LegalPage, type LegalSection } from "@/components/legal-page";
import { OPERATOR, REFUND_WINDOW_DAYS, TRIAL_DAYS } from "@/lib/legal";

export const metadata: Metadata = {
  title: "Refunds & Cancellation - FIG",
  description: "How to cancel FIG, when you can get a refund, and how billing changes are handled.",
  alternates: { canonical: "/refunds" },
};

/**
 * Written from how billing really behaves, so it can be kept honest:
 *  - cancelling is "at period end" (the live Stripe customer portal is set to
 *    that, with no proration credit on cancel);
 *  - changing the number of sites is prorated (`sync_quantity` uses
 *    `create_prorations`);
 *  - no card is taken at sign-up, so a trial cannot bill by surprise.
 * The 14-day money-back window is a business decision, not a legal minimum;
 * change `REFUND_WINDOW_DAYS` in lib/legal.ts to change it everywhere.
 */
const sections: LegalSection[] = [
  {
    id: "trial",
    title: "The free trial",
    body: (
      <p>Every new account starts with a free trial of <strong>{TRIAL_DAYS} days</strong>. We do not ask for a card to start it, so nothing can be charged until you choose to subscribe. If you never subscribe, you are never billed.</p>
    ),
  },
  {
    id: "cancel",
    title: "How to cancel",
    body: (
      <>
        <p>You can cancel any time, without contacting us and without a reason:</p>
        <ol>
          <li>Sign in and open <strong>Settings → Billing</strong>.</li>
          <li>Choose <strong>Manage billing</strong>. This opens our payment provider&rsquo;s secure page.</li>
          <li>Choose the option to <strong>cancel your plan</strong> and confirm.</li>
        </ol>
        <p>Cancelling stops future charges. <strong>Your subscription runs to the end of the period you have already paid for</strong>, and you keep access until then. It does not renew, and we do not charge you again. We do not refund the unused part of a period you chose to end early, except as set out below.</p>
      </>
    ),
  },
  {
    id: "refund",
    title: "When you can get a refund",
    body: (
      <>
        <Callout>
          <p><strong>{REFUND_WINDOW_DAYS}-day money-back guarantee.</strong> If FIG is not right for you, ask within {REFUND_WINDOW_DAYS} days of your <em>first</em> payment and we will refund that payment in full, no questions asked.</p>
        </Callout>
        <p>Beyond that window we will also refund:</p>
        <ul>
          <li><strong>Charges made in error</strong>, such as a duplicate payment or a charge after you had cancelled in time.</li>
          <li><strong>Charges for a period in which FIG was not usable</strong> because of a fault on our side that we could not fix in a reasonable time. We will refund the affected part.</li>
          <li>Anything the law requires us to refund where you live. Nothing here limits your statutory consumer rights, including any right to cancel and be refunded that applies where you live.</li>
        </ul>
        <p>Otherwise, payments for a period that has already started are not refundable. Renewals are not covered by the {REFUND_WINDOW_DAYS}-day guarantee, which is why cancelling is kept to a few clicks and you can do it at any time before the next charge.</p>
      </>
    ),
  },
  {
    id: "sites",
    title: "Adding or removing sites",
    body: (
      <>
        <p>FIG is billed per active site, so your charge follows the number of sites in your workspace. When you add a site partway through a billing period, you pay the extra amount for the rest of that period, prorated. When you remove one, the unused part is credited against your next invoice.</p>
        <p>Removing a project stops monitoring and billing for it. The history stays in your account until you ask us to delete it.</p>
      </>
    ),
  },
  {
    id: "how",
    title: "How to ask for a refund",
    body: (
      <>
        <p>Email <strong>{OPERATOR.email}</strong> from the address on your account, with the date of the charge if you have it. We aim to reply within <strong>2 business days</strong>.</p>
        <p>Approved refunds go back to the <strong>original payment method</strong>. Your bank or card issuer usually shows it within <strong>5 to 10 business days</strong>; how long it takes after we issue it is up to them. Fees and currency conversion are handled as your card issuer applies them.</p>
      </>
    ),
  },
  {
    id: "disputes",
    title: "If something looks wrong",
    body: (
      <p>Please contact us first. We can usually fix a billing problem faster than a bank dispute can, and we would rather refund a mistake than argue about it. Related: <Link href="/terms">Terms of Service</Link> and <Link href="/privacy">Privacy Policy</Link>.</p>
    ),
  },
];

export default function RefundsPage() {
  return (
    <LegalPage
      path="/refunds"
      title="Refunds & cancellation"
      intro={<p>The short version: there is no card at sign-up, you can cancel in a few clicks, and your first payment is refundable for {REFUND_WINDOW_DAYS} days. The details are below so nothing about billing is a surprise.</p>}
      sections={sections}
    />
  );
}
