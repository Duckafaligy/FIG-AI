import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight, BriefcaseBusiness, GraduationCap } from "lucide-react";
import { PLANS } from "@/lib/plans";
import styles from "./audience-spotlight.module.css";

export function AudienceSpotlight() {
  return <div className={styles.grid}>
    <article className={`${styles.card} ${styles.business}`}>
      <div className={styles.visual}>
        <Image src="https://images.unsplash.com/photo-1758873268745-dd2cf0d677b5?auto=format&fit=crop&w=1000&q=85" alt="Colleagues reviewing a website together at a computer" fill sizes="(max-width: 800px) 100vw, 50vw" />
        <span className={styles.badge}><BriefcaseBusiness size={15} />FIG for business</span>
        <div className={styles.imageCaption}>Your website.<br /><em>Your next opportunity.</em></div>
      </div>
      <div className={styles.content}><span className={styles.kicker}>Built for owners & teams</span><h3>Make your website<br />work harder for you.</h3><p>See your website with fresh eyes. Turn clear, actionable findings into a more confident online presence.</p>
        <div className={styles.tags}><span>Analyze your site</span><span>Find what to improve</span></div>
        <div className={styles.bottom}><div className={styles.price}><small>Business plans from</small><strong>${PLANS.find(p => p.name === "Standard")!.price}<span> USD / month</span></strong></div><Link href="/pricing#business">Explore business<ArrowUpRight size={19} /></Link></div>
        <div className={styles.planNames}>Standard · Premium · Enterprise</div>
      </div>
    </article>
    <article className={`${styles.card} ${styles.education}`}>
      <div className={styles.visual}>
        <Image src="https://images.unsplash.com/photo-1758876021859-bd2371d8f0a2?auto=format&fit=crop&w=1000&q=85" alt="A person exploring ideas and working at a laptop" fill sizes="(max-width: 800px) 100vw, 50vw" />
        <span className={styles.badge}><GraduationCap size={17} />FIG for education</span>
        <div className={styles.imageCaption}>Stay curious.<br /><em>Build something better.</em></div>
      </div>
      <div className={styles.content}><span className={styles.kicker}>For learners & classrooms</span><h3>Don’t just browse websites.<br />Understand them.</h3><p>Explore the thinking behind better websites. Connect design, structure, and search through real-world analysis.</p>
        <div className={styles.tags}><span>Learn by exploring</span><span>Build your understanding</span></div>
        <div className={styles.bottom}><div className={styles.price}><small>Education</small><strong>${PLANS.find(p => p.name === "Education")!.price}<span> USD / month</span></strong></div><Link href="/pricing#education">Explore education<ArrowUpRight size={19} /></Link></div>
        <div className={styles.planNames}>Individual learners · School Registered</div>
      </div>
    </article>
  </div>;
}
