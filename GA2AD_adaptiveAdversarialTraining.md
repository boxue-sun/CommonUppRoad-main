# Nature Communicationshttps://doi.org/10.1038/s41467-026-75643-z

# Article in Press

# GA2AD: a generalized adaptive adversarial training

# framework considering surrounding hybrid risk

# field for autonomous driving

Received: 26 February 2025Haocheng Xu, Yusheng Ci, Yunfei Long, Ci Liang, Lina Wu, Xiqun Chen, Mohamed Ghazel Accepted: 7 July 2026& Lei Feng

Cite this article as: Xu, H., Ci, Y., Long,We are providing an unedited version of this manuscript to give early access to its Y.et al. GA2AD: a generalizedfindings. Before final publication, the manuscript will undergo further editing. Please adaptive adversarial trainingnote there may be errors present which affect the content, and all legal disclaimers framework considering surroundingapply. hybrid risk field for autonomous If this paper is publishing under a Transparent Peer Review model then Peer driving.Nat Commun (2026). https:// Review reports will publish with the final article. doi.org/10.1038/s41467-026-75643-z

# ARTICLE IN PRESS

© The Author(s) 2026. Open Access This article is licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License, which permits any non-commercial use, sharing, distribution and reproduction in any medium or format, as long as you give appropriate credit to the original author(s) and the source, provide a link to the Creative Commons licence, and indicate if you modified the licensed material. You do not have permission under this licence to share adapted material derived from this article or parts of it. The images or other third party material in this article are included in the article's Creative Commons licence, unless indicated otherwise in a credit line to the material. If material is not included in the article's Creative Commons licence and your intended use is not permitted by statutory regulation or exceeds the permitted use, you will need to obtain permission directly from the copyright holder. To view a copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/4.0/.

### ARTICLE IN PRESS

## GA2AD: A Generalized Adaptive Adversarial

## Training Framework Considering Surrounding

## Hybrid Risk Field for Autonomous Driving

11*21* Haocheng Xu, Yusheng Ci, Yunfei Long, Ci Liang, 3*456 Lina Wu, Xiqun Chen, Mohamed Ghazel, Lei Feng

1* School of Transportation Science and Engineering, Harbin Institute of Technology, 73 Huanghe Road, Nangang District, Harbin, 150090, Heilongjiang, China. College of Computer Science and Technology, Harbin Engineering University, 145 Nantong Street, Nangang District, Harbin, 150001, Heilongjiang, China. 3* School of Automobile and Traffic En gineering, He ilongjiang Institute of Technology, 999 Hongqi Street, Daowai District, Harbin, 150050, Heilongjiang, China. Institute of Intelligent Transportation Systems, College of Civil Engineering and Architecture, Zhejiang University, 866 Yuhangtang Road, Xihu District, Hangzhou, 310058, Zhejiang, China. 5COSYS/ESTASDepartment,Universite´GustaveEiffel,5Boulevard Descartes, Villeneuve-d’Ascq, 59650, France. School of Industrial Engineering and Management, KTH Royal Institute of Technology, 8 Brinellv¨agen, Stockholm, 11428, Sweden.

*Corresponding author(s). E-mail(s): ciyusheng@hit.edu.cn;

# ARTICLE IN PRESS

liangci321@hit.edu.cn; wulina@hljit.edu.cn; Contributing authors: 23B932009@stu.hit.edu.cn; 2016064109@hrbeu.edu.cn; chenxiqun@zju.edu.cn; mohamed.ghazel@univ-eiffel.fr; lfeng@kth.se;

Abstract Ensuring autonomous vehicle safety in mixed traffic re mains di fficult because human-driven vehicles can create rare and unpredictable interactions that are

### ARTICLE IN PRESS

underrepresented in conventional training. Here we present GA2AD, a gen- eralized adaptive adversarial training framework that generates challenging but controllable driving scenarios for autonomous vehicle decision-making. The framework treats the target autonomous vehicle model as a black box and trains a background-vehicle model to create adversarial maneuvers, including cutting in, hard braking and speeding. A hybrid risk field estimates the interaction risk imposed by surrounding vehicles, while an activation function selects when adver- sarial maneuvers should be applied. An adaptive switching module alternates training between the target vehicle and the background-vehicle model according to collision intervals, avoiding overly weak or overly severe adversarial condi- tions. In simulation, GA2AD reduces collision rates by 55–70% and lowers the 95th percentile absolute jerk by 21–42%, with only small decreases in average speed. Tests on an autonomous vehicle track using synchronized virtual traffic further show improved safety and comfort under the tested adversarial condi- tions. These results indicate that adaptive adversarial scenario generation can improve autonomous vehicle robustness in complex mixed traffic.

Keywords: Autonomous Driving, Generalized Adaptive Adversarial Training, Reinforcement Learning, Mixed Traffic Safety

### Introduction

Rapid advancements in the autonomous vehicle industry have led to many commercial deployments, resulting in a new era of mixed traffic that combines both Autonomous Vehicles (AVs) and Human-Driven Vehicles (HDVs). However, such a mixed traf- fic p oses s ubstantial c hallenges, p articularly i n t erms o f e nsuring s afety w ithin these heterogeneous traffic en vironments [1 ]. Sp ecifically, the beh avior of HDV s inherently shows considerable variability due to the diverse nature of human drivers, some of whom may even engage in traffic vi olations. On th e ot herha nd, in troducing AVs fundamentally changes traffic dy namics, le ading to ne w pa tterns in tr affic flow, thus requiring human drivers to adapt their behaviors accordingly, which heightens the unpredictability associated with human drivers. Such a rise in behavioral discrep- ancy substantially affects t he i nteractions b etween h eterogeneous v ehicles, thereby hampering safety in mixed traffic [2]. The safety challenges in mixed traffic flo ws mai nly ari se fro m the behavioral variability of human-driven vehicles, their possible traffic ru le vi olations, an d insuf-

# ARTICLE IN PRESS

ficient i nteraction w ith a utonomous v ehicles. H uman-driven v ehicles m ay display unpredictable behaviors that vary across drivers, leading to irregular and sometimes hazardous traffic co nditions [3 ]. Th ey ma y al so co mmittr affic infr actions,such as speeding or disobeying traffic si gnals, wh ich di srupt tr affic orde rand chal lenge the programmed expectations of autonomous vehicles [4]. In addition, insufficient com- munication and limited cooperative patterns between autonomous and human-driven vehicles can lead to misjudgments and conflicts [5]. Researchers have employed various methods to tackle the above issues, including assessing risks in mixed traffic [6–8], predicting behaviors of surrounding vehicles [9],

### ARTICLE IN PRESS

or further establishing game-theoretic models between AVs and nearby HDVs to make appropriate decision [10]. Nevertheless, owing to the curses of dimensionality and rarity of safety-critical events in mixed traffic situations, these approaches often lack robust- ness, the ability to reliably handle complex and challenging behaviors, and are thus particularly vulnerable to corner cases, which present bottlenecks in their reliability and effectiveness 11].[ To address the challenges mentioned above, adversarial methods have been widely studied to improve model robustness against perturbations and adversarial attacks, which is applied in various deep learning domains including computer vision [12, 13] and natural language processing [14]. In the context of autonomous driving, researchers have developed adversarial approaches [15] to increase the robustness of AVs across three key functional aspects, i.e. perception, decision-making, and actuation. These approaches are applicable to both modularization [9, 16, 17] and end-to-end [6] archi- tectures. In terms of perception, adversarial methods, such as data poisoning, attack target sensor systems to test their robustness. In terms of actuation, disturbances are introduced to vehicle outputs (e.g., steering, acceleration, and braking) to assess response reliability under various conditions [18, 19]. In terms of decision-making which is the focus of this paper, adversarial reinforcement learning has emerged as a promis- ing paradigm for improving model robustness by simulating worst-case disturbances during agent training [20, 21], which typically involve a generator and a discrimina- tor like generative adversarial networks. The generator produces decisions, while the discriminator evaluates these decisions to differentiate b etween v ulnerable a nd invul- nerable decisions, in turn, guiding the generator in refining its decision-making strategy by identifying the weaknesses of the generator and applying adversarial actions [22]. Nonetheless, these conventional adversarial methods, including generative adversar- ial network (GAN)-based approaches, often require access to target model’s internal states or gradients for training, as they rely on simultaneous updates and shared information between components, which limits their generalizability across different model architectures and scenarios. Additionally, directly applying adversarial attacks (e.g., aggressive maneuvers from background vehicles) without adaptive control over their adversarial intensity often causes AV safety mechanisms to fail, as non-adaptive attacks may be too weak to expose vulnerabilities or excessively strong to be handled safely by the AV model. This highlights the need for solutions that are broadly appli- cable across various vehicle models and scenarios to promote robustness and enhance safety in mixed traffic environments [23–25]. In this work, we present a Generalized Adaptive Adversarial training frame-

# ARTICLE IN PRESS

work for Autonomous Driving (GA2AD), an adaptive adversarial training method for improving autonomous vehicle robustness in mixed traffic. GA 2AD tr eats the target autonomous vehicle model as a black box and trains a background-vehicle model to generate challenging but controllable adversarial interactions. The frame- work combines a hybrid-risk-field-based inverse risk assessment, an activation function for selecting appropriate adversarial conditions, and an adaptive switching mecha- nism that alternates training between the target vehicle and the background vehicles according to collision intervals. We evaluate GA2AD in simulation across multiple

### ARTICLE IN PRESS

reinforcement-learning-based target vehicle models and further conduct vehicle-in-the- loop field t ests w ith s ynchronized v irtual t raffic. The res ults sho w red uced collision rates and smoother driving under the tested adversarial conditions, while maintaining operational efficiency.

### Results

GA2AD framework

In this study, we propose the GA2AD, which constructs adversarial scenarios where an adversary agent strategically manipulates interactions between vehicles. This adver- sarial approach treats any reinforcement learning (RL)-based AV model, namely the Target Vehicle (TV) model, as a black box, and focuses on enhancing its defensive capabilities against adversarial actions as shown in Fig. 1a. Notably, the scope of GA2AD focuses on proactive collision avoidance and risk mitigation during inter- actions, rather than assessing GA2AD’s performance impact on post-crash outcome severity (e.g., ∆v or injury risk). Specifically, we define vehicles that surround the TV and interact with it as Back- ground Vehicles (BVs), as shown in the top left corner of Fig. 1b. Among these BVs, an Adversarial Background Vehicle (ABV) is dynamically selected to perform adversarial maneuvers, creating challenging scenarios to test and enhance the TV’s robustness. A corresponding BV model is proposed to dynamically adjust the maneuvers of BVs, which consists of two parts, the RL-based BV model and the rule-based BV model. At each simulation timestep, our GA2AD utilizes the rule-based BV model to con- trol BVs at first to establish a normal training environment. And the ABV candidate and the corresponding ABV’s maneuver are determined by the RL-based BV model. Additionally, the inverse risk assessment module and the activation function module serve as supplements to the BV model, as shown in Fig. 1b. To evaluate whether the ABV candidate is appropriate, the framework introduces an inverse risk assessment to analyze the risk of each BV on the TV. In detail, the hybrid risk field considering states of the TV is proposed based on the traditional risk field a s s hown i n F ig. 1c, w hich a llows f or a m ore p recise a ssessment o f t he individ- ual risks of BVs to TV. The Bayesian Theory is utilized to calculate the individual risk of the ABV candidate and the holistic risk jointly caused by all BVs using the predefined p rior p robability o f d ifferent ri sk le vels, na mely da ngerous, at tentive and safe. The individual risk of the ABV candidate and the holistic risk are then fed into

# the activation ARTICLE IN PRESSfunction, ensuring it neither too conservative nor too aggressive. If the

result of the activation function falls between the predefined upper and lower bounds, the ABV’s original maneuver will be replaced by an adversarial maneuver such as cut in, hard braking and speeding. This induces a complex adversarial scenario that chal- lenges the TV’s robustness against both direct threats and the resulting environmental perturbations. These interactions are used as training inputs for the BV model only when the ABV performs adversarial maneuvers, namely f (ϵb, ϵenv) = 1 in Eq. (21), which ensures that the BV model learns from challenging and risky scenarios. Since a too conservative ABV can hinder the TV learning process, whereas overly aggressive

### ARTICLE IN PRESS

Fig. 1 The proposed GA2AD framework. a, Architecture and training process of the GA2AD frame- work environment. b, Example of adversarial environment generation. c, Inverse risk assessment, including the traditional risk field, h ybrid r isk fi eld co nsidering TV st ates, an d Ba yesian pr ior prob- ability of Dangerous, Attentive, and Safe risk levels. d, Illustration of the adaptive switch module, in which training phases alternate based on collision episode interval thresholds, indicated by the dashed red line.

ABV can lead to the TV training failure, such a trade-off i n t he A BV s election can help the BV model identify appropriate candidates and behaviors. The training process for the TV and BV models, formulated as a two-player Markov Decision Process (MDP), is inherently prone to instability. To address this issue, we propose an adaptive switch module (ASM), as illustrated in Fig. 1a, which enables an

# alternatingtrainingARTICLE IN PRESSmechanismbetweentheTVandBVmodels.Duringeachtraining

phase, when the TV model is being updated, the BV model freezes its parameters, and vice versa. This design reduces the interference caused by simultaneous policy updates, a well-known challenge in multi-agent reinforcement learning that can lead to unstable training and convergence issues [26, 27]. In doing so, the multi-agent problem effectively transforms into a single-agent RL task, enhancing both the stability and timeliness of the training process for the two models. Meanwhile, to further ensure that the BV model does not become overly aggressive or excessively conservative, the adaptive switch module also leverages the collision episode interval (defined as the episode between two successive TV collisions

### ARTICLE IN PRESS

during training process) as a key switching criterion. In Fig. 1d, the module segments the collision rate curve into two regions at a threshold made of collision episode inter- val: the above for the TV model training and the below for updating the BV model. By dynamically adjusting the BV’s adversarial intensity based on the TV’s safety per- formance measured through the collision episode interval, the framework ultimately improves the training efficiency an d sa feguards th e TV fr om be ing ov erwhelmed by excessively aggressive adversarial behaviors. Specifically, with such a mechanism, when the TV experiences frequent collisions, the system is able to reduce adversarial inten- sity by prioritizing TV training and limiting the aggressiveness of the ABVs. This mechanism ensures stable learning progress and prevents TV from being exposed to unrealistic or unmanageable threats during early stages of training. Based on the normal training environment only with the rule-based BV model, this study proposes an adaptive adversarial training framework GA2AD that integrates RL-based BV model as the adversarial maneuvers generator, along with an activation function with the inverse risk assessment as the adversarial maneuvers discriminator to create an appropriate adversarial training environment for the TV model.

Training dynamics

This section analyzes the alternative training process of the TV and BV models under the ASM in the GA2AD framework. Through alternating training cycles, the TV progressively adapts to the adversarial strategies of the BV model, which concur- rently enhances its own adversarial capabilities. The evaluation metrics reveal how the framework enhances TV performance by introducing increasingly challenging adver- sarial scenarios. As shown in Fig. 2, the red curves indicate training processes for BV, whereas the blue curves represent those for the TV, illustrating differential strategies of alternating training processes and performance metrics over training episodes. As shown in Fig. 2a, at the beginning of the training process I, the collision rate of the TV model is high. As the collision rate gradually decreases, the adaptive switch function is activated, initiating the training for the BV model, which leads to an increase in the collision rate again. This increase in the frequency of collision triggers the adaptive switch function once more, prompting the further training of the TV model. This results in a renewed decrease in the collision rate. This cycle continues until the training converges. Fig. 2b illustrates a clear pattern of the average speed of the TV during the alternating training process: each time the BV model undergoes training, there is a

# noticeable decreaseARTICLE IN PRESS in the TV’s average speed. Initially, the average speed gradually

increases with the training process of the TV model, but it soon experiences a rapid decline in speed during the first training session I of the BV model, illustrating direct disruption of ABV’s maneuvers on the TV, and introducing new challenges or obstacles that temporarily reduce its speed. As the TV model resumes its own second training process II, the average speed generally increases, reflecting p eriods of adjustment and improvement in its driving algorithms. Notably, the marked speed decline during the BV part of the third training process III suggests that the challenges posed by the BV model’s training grow more complex and adversarial as the training progresses.

### ARTICLE IN PRESS

ab

2.535 I II III IV 30I II III IV 2.0

1.5

1.0

0.5TV Training10 Collision Rate (10e-6)Average Speed (m/s) BV Training 0.0

0 200 400 600 8000 200 400 600 800 EpisodeEpisode

cd

1.01.0 I II III IV I II III IV 0.8 0.8 (m/s³) 0.6 th0.6 | 0.4 Jerk0.4 | 0.2Environmental Risk 0.2 0.0

0 200 400 600 8000 200 400 600 800 EpisodeEpisode

Fig. 2 Visualization of the alternative training process for the TV and BV under the ASM via the GA2AD framework. a, Collision rate variation of the TV. b, Average speed variation of the TV. c, Variation of the 95th percentile absolute jerk of the TV. d, Environmental risk variation of the TV. Numerical values represent the mean environmental risk across different t raining s tages. L ight grey lines represent the raw data before exponential smoothing. Source data are provided as a Source Data file.

As shown in Fig. 2c, the 95th percentile absolute jerk of the TV gradually stabilizes during the training process, suggesting that the TV model learns more stable driving behaviors even in the BV training process. In the first t raining p rocess I , t he 95th percentile absolute jerk shows slight fluctuations. However, the 95th percentile absolute jerk in the beginning stage of the TV training process II sharply increases, indicating that the TV encounters much more challenging situations because of the adversarial behaviors of the ABV. As the TV model continues its third and fourth training process III and IV, the 95th percentile absolute jerk gradually decreases, indicating that the TV model obtains the ability to defend against the interventions from the ABV. Fig. 2d illustrates the evolution of the environmental risk of the TV model at different t raining s tages, w ith numerical values p ositioned a bove o r b elow e ach curve indicating the mean environmental risk for the corresponding stage. There is a climb in the first t raining p rocess I r eaching a p eak f ollowed b y a c onsistent d ecrease in

# the environmental riskARTICLE IN PRESS in each TV training session after the finish of the BV training

session, suggesting that the training scenarios implemented by the BV model create conditions that temporarily elevate the environmental risk for the TV model. More complex adversarial scenarios introduced by the ABV challenge the TV’s ability to maintain safety, facilitating its adaptation to more risky situations. These trends above illustrate a co-evolution between the TV and BV models in the adversarial training setup. The TV model continuously adapts to challenges posed by the BV model, while the BV model strategically enhances its adversarial tactics. This alternating training mechanism allows each model to continually refine i ts strategies, enhancing the overall performance and robustness of the framework.

### ARTICLE IN PRESS

Additionally, our trained BV model is aware of the inverse risk on the TV to take proper adversarial actions to potentially cause collisions, as shown in Fig. 3a. The same ABV candidate is selected to take a series of adversarial actions to raise the risk level, as shown in Fig. 3b. At t = 0 s, the initial risk assessment indicates a baseline level of risk as the BV and TV begin their interaction. At this moment, the risk level is relatively low, thus the activation function is not activated. By t = 0.7 s, a notable decrease in the relative distance between the BV and TV causes a sudden increase in the risk field intensity, which is detected by the inverse risk assessment. The activation function is triggered, and the adversarial actions begin to influence t he T V’s driving state. As the BV continues to take adversarial actions, specifically acceleration, which further increases the risk. This acceleration leads to a subsequent leap in the risk field at t = 2.2 s, as the relative longitudinal speed between the BV and TV increases abruptly. This leads to near-missing situations and eventually causes a collision at t = 3.4 s. These snapshots in Fig. 3a demonstrate the GA2AD framework specifically trains the TV to anticipate and safely react to adversarial behaviors from any BV, including those positioned to the rear, left-rear, or right-rear. By exposing the TV to these risky scenarios through adversarial training, we illustrate how such BV actions increase driving difficulty for the TV, ultimately improving defensive responses of the TV.

Cross-validation

This section presents a comparison of TV model performance metrics across different training and testing strategies. We define t he t raining p rocess o f t he G A2AD a s the adversarial training process. After adversarial training, the trained BV model contin- ues to construct the adversarial test process. In contrast, the training process that no BV model is trained, which consists of only the default setting, is considered as a nor- mal training process. Similarly, the testing process without the trained BV model is the normal testing process. Then we compared the TV performances between normal and adversarial training under the normal and adversarial testing conditions. As shown in Fig. 4, we consider four combinations of training and testing processes: NN represents Normal Training + Normal Testing, serving as the baseline of the TV performance under the conditions of normal training and testing; AN denotes Adversarial Training
+ Normal Testing, indicating enhanced performance of the TV model due to adver- sarial training methods during the normal testing; NA indicates Normal Training + Adversarial Testing, indicating performance drops of the normally trained TV due to

# insufficient responsesARTICLE IN PRESS for adversarial conditions; AA corresponds to Adversarial Train-

ing + Adversarial Testing, underlining the robustness advantage of the adversarially trained TV in challenging scenarios of adversarial testing. As shown in Fig. 4a, the adversarially trained TV model (refer to AN and AA) achieves lower collision rates than those trained in normal environments (refer to −6 NN and NA). Notably, the baseline NN collision rate (1 × 10/km) is lower than −6 real-world benchmarks from China’s Demonstration Zones (≈ 6.48 × 10/km) [28]. Note that such a discrepancy between simulation conditions and real-world driving conditions may arise potentially because simulated BVs in normal environment lack behavioral uncertainty and execute conservative driving actions, making the emergence

### ARTICLE IN PRESS

a ABVt = 0.1 st = 0.4 s t = 0.7 s t = 1.0 s TV

t = 1.3 s t = 1.6 s t = 1.9 s t = 2.2 s

t = 2.5 s t = 2.8 s t = 3.1 s t = 3.4 s

b 1.0 SafeExpected Risk of the ABV 1.50 0.8Attentive Dangerous1.25 0.6 1.00 0.4 0.75 Probability 0.20.50

Expected Risk of the ABV 0.00.25 0.5 1.0 1.5 2.0 2.5 3.0 Time (s)

Fig. 3 Visualization of a rear-end collision caused by an ABV from the left rear. a, Snapshots of the hybrid risk field, shown at the top, and the relative positions of the ABV and TV, shown at the bottom. b, Temporal changes in the posterior probabilities of Safe, Attentive, and Dangerous risk levels, computed by Eq. (14), and the ABV expected risk ϵb, computed by Eq. (19)(range 0–2). Source data are provided as a Source Data file.

of high risky scenarios scarcer than those in real world. Additionally, different traffic cultures in different regions may impact crash rates, which also need to be considered in further work. As illustrated in Fig. 4b, adversarial training also reduces the 95th percentile abso- lute jerk. The TV models trained in a normal setup (refer to NN and NA) exhibit the 95th percentile absolute jerk of about 0.301 and 0.347, respectively. In contrast,

# adversarially trained TV models (refer to AN and AA) show reduction of 21.23% andARTICLE IN PRESS

42.35%, respectively. This reduction highlights the ability of adversarial training to improve TV’s ability to enable smooth and comfortable maneuvers. Fig. 4c shows that for TVs tested in normal condition, the average speed in AN is slightly decreased by 2.9 m/s, which corresponds to a reduction of only 9.18% com- pared with that in NN, highlighting the improved caution of adversarially trained TVs while still preserving traffic efficiency. Similarly, under adversarial testing conditions, the slight average speed reduction between NA and AA is 1.2 m/s, which corresponds to a decrease of merely 4.24%, indicating the robustness of adversarial training in han- dling adversarial scenarios with minimal compromise in traffic efficiency. These results

### ARTICLE IN PRESS

underscore the balance between safety and traffic effi ciency achi eved by adversarial training, namely ensuring safety without sacrificing speed. As shown in Fig. 4d, the environmental risk is greater under the normal training process (refer to NN and NA) than that under the adversarial training (refer to AN and AA). Specifically, the risk decreases from 0.44 in NN to 0.41 in AN, which represents a reduction of 6.82% in normal testing. Additionally, it decreases from 0.57 in NA to 0.51 in AA, reflecting a r eduction o f 1 0.53% i n a dversarial t esting. O verall, adversarially trained TVs show a better adaptability in effectively managing risks in unpredictable conditions, even in the adversarial testing scenarios with higher environmental risks (refer to NA and AA) than those in normal testing scenarios (refers to NN and AN). In summary, adversarial training enhances the safety performance of TV models, with collision rate dropping by 69.31% in AN scenarios and 55.24% in AA scenarios. Although it modestly reduces average speeds by 2.9 m/s (reduction of 9.18%) in AN and 1.2 m/s (reduction of 4.24% ) in AA, the trade-off is justified by the considerable gains in safety and robustness. This slight decrease in speed is both manageable and acceptable, affirming th e va lue of ad versarial tr aining in ch allenging environments.

Generalization analysis

We further assess the generalization of the GA2AD framework to the TV model which varies on different R L a lgorithms.To d emonstrate t he G A2AD framework’s compatibility with diverse state-of-the-art RL approaches for AV decision-making, we evaluated TV models by employing different d eep r einforcement l earning algorithms. In addition to the off-policy a nd value-based D eep Q -Network ( DQN) a lgorithm, we analyzed the model performance using off-policy and actor-critic methods such as the Twin Delayed Deep Deterministic Policy Gradient (TD3) [29], the Soft Actor-Critic (SAC) [30], and the Deep Deterministic Policy Gradient (DDPG) [31]. These evalu- ations were conducted in both normal and adversarial test environments to compare the performance gap between adversarially and normally trained TV models across different algorithms using the four p erformance indicators defined in Evaluation met- rics. The gap represents the difference in TV performance metrics between adversarial training (AA, AN) and normal training (NN, NA) in terms of various RL-algorithm TV models, i.e., Gap in Adversarial Test = Metric(NA) - Metric(AA), Gap in Normal Test = Metric(NN) - Metric(AN). A larger gap in collision rate, the 95th percentile absolute jerk, environmental risk indicates greater improvement about safety and com- fort due to adversarial training. And a smaller gap in average speed indicates loss of

# operational efficiency.ARTICLE IN PRESS

Fig. 5 illustrates the differences o n t he f our m etrics w hen t he R L a lgorithms for controlling the TV are DQN, TD3, SAC, and DDPG. Since the differences between the studied RL algorithms are small, the results suggest the generalizability of the GA2AD adversarial training framework. In both normal and adversarial testing envi- ronments, the GA2AD consistently achieves better results in collision rate, the 95th percentile absolute jerk, and environmental risk, affirming its ca pability of enhancing safety and stability for different m odels. M oreover, u nder a dversarial t esting, these three metrics exhibit greater reductions compared to normal testing, indicating that the framework achieves improved safety and driving comfort in adversarial scenarios.

### ARTICLE IN PRESS

ab

↓55.24%

0.40

−5↓42.35% ↓21.23% )0.35 s / m ( ↓69.31%0.30 95th

Collision Rate* |Jerk| −60.25

0.20

NN AN NA AANN AN NA AA

cd

35.0↓9.18% 0.65 ↓10.53% 32.5 ↓4.24%0.60 ) /s m30.0 (0.55

27.5↓6.82% 0.50

25.0 Environmental Risk Average Speed0.45

22.5 0.40

20.0 0.35

NN AN NA AANN AN NA AA

Fig. 4 Cross-validation analysis of TV performance. Results are shown across four combinations of training and testing environments: Normal Training + Normal Testing (NN), Adversarial Training
+ Normal Testing (AN), Normal Training + Adversarial Testing (NA), and Adversarial Training
+ Adversarial Testing (AA). The evaluated metrics include collision rate (a), the 95th percentile absolute jerk (b), average speed (c), and environmental risk (d). The y axes in a use logarithmic scales. Source data are provided as a Source Data file.

While a reduction in average speed is observed across all algorithms, the impact on driving efficiency re mains mi nimal an d ac ceptable. No tably, as sh own in Fi g. 5c, the speed reduction under adversarial testing is smaller than that in normal testing, fur- ther supporting the framework’s balanced optimization of safety and efficiency. The negligible differences i n average s peed u nder a dversarial t esting a re a chieved through

# adversarial training.ARTICLE IN PRESS The reward function of TV model emphasizes both safety and

efficiency by re warding th e TV mo del fo r ma intaining sp eed ar ound th e de sired level and penalizing unnecessary fluctuations. D uring a dversarial t raining, t he T V model encounters diverse challenging scenarios, prompting it to develop robust speed control strategies. The TV model learns to anticipate potential threats from ABV maneuvers and proactively adjusts speed of the TV to avoid collisions. More specifically, D DPG s tands o ut f or i ts b etter p erformance i n r educing colli- sion rates under normal conditions, as shown in Fig. 5a. As for the 95th percentile absolute jerk, TD3 outperforms other algorithms in Fig. 5b. The SAC results in a

### ARTICLE IN PRESS

notable reduction in environmental risk while maintaining a relatively slight reduction of average speed, as indicated in Fig. 5c and d. The results highlight the generalizability of the proposed GA2AD framework. Com- pared to Adversarial Reinforcement Learning [20] or Fictitious Self Play [32], which often require extensive retraining or specific adaptations for different target agents, GA2AD’s black-box compatibility enables easy integration with a wide array of RL algorithms without architectural modifications, thus showcasing potential generaliz- ability. GA2AD generally improves the safety and comfort of different models, with only a modest reduction in efficiency, which remains within an acceptable range.

ab

Normal Test 1.40.175 Adversarial Test

1.20.150 ) −7) 1.0/s0.125 (10 m ( 0.895th0.100

|Jerk| 0.60.075

Gaps in Gaps in Collision Rate0.40.050

0.20.025

0.00.000 DQN TD3 SAC DDPGDQN TD3 SAC DDPG

cd

3.0 0.07

2.50.06 ) s / m (0.05 2.0

0.04 1.5

0.03

1.0 Gaps in Environmental Risk Gaps in Average Speed0.02

0.5 0.01

0.00.00 DQN TD3 SAC DDPGDQN TD3 SAC DDPG

# ARTICLE IN PRESS

Fig. 5 Results of the generalization validation experiment. a–d, Performance gaps between normal and adversarial training under normal testing (NN–AN) and adversarial testing (NA–AA) for DQN, TD3, SAC, and DDPG. The evaluated metrics include collision rate (a), the 95th percentile absolute jerk (b), average speed (c), and environmental risk (d). Larger gaps in a, b, and d indicate stronger robustness of the TV, whereas smaller gaps in c indicate a smaller effect on TV driving efficiency. Source data are provided as a Source Data file.

### ARTICLE IN PRESS

Ablation study

The adaptive switch module in the GA2AD framework dynamically adjusts the train- ing durations of the BV and TV models based on the TV’s safety performance, in contrast to fixed-time-slot methods like those in [20]. Fig. 6a illustrates the reward per- formance of the TV model under different t raining s etups, i ncluding n ormal training (NT), the proposed GA2AD, and three fixed-switch-interval adversarial training vari- ants. Specifically, AT-100, AT-200, and AT-400 denote adversarial training variants in which the training process is alternately switched between the TV and BV models at fixed intervals of 100, 200, and 400 episodes, respectively. The NT serves as the base- line, operating in a less hazardous environment without ABVs. Consequently, the TV in the NT environment achieves rapid convergence to a stable and high reward level early in the training process due to the absence of adversarial behaviors. In contrast, the GA2AD framework incorporates adversarial risk states introduced by ABVs, which initially cause a drop in the TV’s reward due to the challenging scenarios. However, through adaptive training, GA2AD enables the TV model to recover and achieve a stable reward level comparable to NT, demonstrating its ability to handle adversarial conditions effectively. Fixed-time-slot alternating training methods (AT-100, AT-200, and AT-400) perform poorly, exhibiting lower rewards and unstable convergence even after extended training. The longer the fixed-time-slot i nterval ( e.g., AT-400), the worse the performance, as these methods fail to adapt to the TV’s learning needs, resulting in consistently low rewards and poor stability. Fig. 6b depicts the environmental risk across different t raining s etups, w ith NT again serving as the baseline. NT exhibits the lowest environmental risk through- out training due to the absence of adversarial behaviors from ABVs. In contrast, GA2AD introduces controlled adversarial scenarios, leading to higher initial environ- mental risk. The fixed-time-slot m ethods (AT-100, AT-200, a nd AT-400) r esult in higher environmental risk, particularly with the longest interval AT-400. We selected AT-400 as the variant GA2AD without the adaptive switch module in the time-to-collision (TTC) distribution comparison shown in Fig. 6c, as it exhibits the most severe training instability, highest environmental risk, and poorest TV per- formance in reward compared to AT-100 and AT-200, thereby providing the strongest contrast to illustrate the necessity of the collision-interval-based adaptive switching module in enhancing training effectiveness and stability. The TTC distribution results in Fig. 6c further support this choice, revealing that AT-400 generates overly aggressive scenarios with notably lower TTC values (mostly less than 1 s), indicating unstable

# andextremeadversarialARTICLE IN PRESSconditions,whereasGA2ADmaintainsamorebalanceddis-

tribution of TTC values, ensuring challenging yet manageable training scenarios that enhance TV robustness without compromising stability. Ablation experiments further indicate the importance of activation function. The role of the activation function is to help the BV model skip irrelevant states and make the BV model trained only from risky states by controlling whether an ABV should perform an adversarial maneuver based on the expected risk level of the surround- ing environment and the selected ABV candidate. As shown in Fig. 6c, the absence of the activation function results in a weakened adversarial intensity compared with GA2AD, leading to a TTC distribution approaching that of NT, which has almost

### ARTICLE IN PRESS

ab

0.7 NT 0.75GA2AD 0.6AT-100 0.50AT-200 AT-400 0.250.5 NT GA2AD 0.00 0.4 AT-100 AT-200 −0.25 AT-4000.3 −0.50Environmental Risk Average Reward of TV 0.2 −0.75

−1.000.1

0 2 4 6 8 10 12 14 160 2 4 6 8 10 12 14 16 Timesteps (10)Timesteps (10)

cd

GA2AD12 GA2AD without Activation function 1.0 GA2AD without Adaptive Switch Module (AT-400) NT

0.8 Increase collisions

Reduce training time 0.6

TTC Frequency0.4Collision Counts

0.22GA2AD GA2AD without Activation function

0.00 0 1 2 3 4 5 60.0 0.5 1.0 1.5 2.0 2.5 3.0 Time to collision (s)Timesteps (105)

Fig. 6 Ablation experiments of GA2AD. a, Comparison of the TV average reward among GA2AD, normal training (NT), and fixed-switch-interval a dversarial t raining variants, i ncluding AT-100, AT- 200, and AT-400, where the numbers indicate fixed switching intervals of 100, 200, and 400 episodes, respectively. b, Comparison of environmental risk among GA2AD, NT, AT-100, AT-200, and AT-
400. c, Comparison of TTC frequency distributions among GA2AD, GA2AD without the activation function, GA2AD without the adaptive switch module (AT-400), and NT. d, Comparison of collision counts caused by the BV model with and without the activation function. Source data are provided as a Source Data file.

no TTC values below 2 s, indicating negligible collision risk, thus providing insuffi- cient challenges to drive robust TV learning. As shown in Fig. 6d, GA2AD reduces the overall training time of the BV model and improves training efficiency. Further- more, the activation function results in an increased frequency of collisions within the

# ARTICLE IN PRESS

same number of time steps. This allows the TV to encounter harder edge cases more efficiently, im proving ro bustness vi a mo re ta rgeted ad versarial training. We further investigated the impact of the activation function’s upper bound Muin the interval [0.1, 1.1] and lower bound Mlin the interval [0.0, 1.0], with a step size of 0.1, on the TV model’s performance. The four key metrics evaluated are average speed in adversarial testing environments, as well as the reduction in collision rate, 95th per- centile absolute jerk, and environmental risk when comparing adversarial training to normal training under adversarial test. Results are shown in Fig. 7. Based on the sen- sitivity analysis of the activation function steepness (detailed in Supplementary Note

### ARTICLE IN PRESS

4 and Supplementary Table 4), the optimal configuration i s a chieved a t k = 3 , with Mu = 0.9 and Ml = 0.1. This setup achieves the best balance between adversarial intensity and training stability, improving safety and comfort metrics while maintain- ing driving efficiency. In detail, when the Mu is set to its maximum value and Ml is set to its minimum value, it is equivalent to the activation function being removed, thus GA2AD cannot achieve optimal adversarial performance as illustrated in the top left corner of the Fig. 7a-d. Additionally, when the two bounds are too close to each other (e.g., Mu = Ml + 0.1), the performance of the GA2AD is quite approximate to that of normal training, where all four performance metrics are at their worst as shown in the dashed red line area in Fig. 7. Specifically, as shown in Fig. 7a, b, and d, when the Ml is set to 0.1 and the Mu to 0.9, the BV model results in the highest collision rate, and the 95th percentile absolute jerk and environmental risk also reach their maxi- mum values. As shown in Fig. 7c, when the Ml is 0.0 and the Mu is 1.1, the reduction of average speed is at its largest. This finding i n F ig. 7 i ndicates t hat t he B V model with an activation function can more effectively achieve adversarial training, with the most pronounced effect o bserved w hen t he M l i s 0 .1 a nd t he M u i s 0 .9, a llowing the BV model to filter o ut s cenes u nlikely t o c ause accident.

Autonomous vehicle field test

To evaluate the efficacy of th e th eoretical me thodology of th e pr oposed GA 2AD, we utilized an augmented-reality supported vehicle-in-loop field t est t echnology, which is widely used for its ability to equip real-world testing with high safety and low cost [11], [33]. As shown in Fig. 8a, the vehicle-in-loop field t est w as c onductedin an urban test route equipped with multiple road scenarios at the Heihe Autonomous Vehicle Test Track, Heilongjiang Province, China. A Dongfeng Chenglong H7 vehicle integrated with a Robot Operating System (ROS)-based autonomous driving system, served as the real AV for test [34]. The real AV’s perception module fuses data from multi-modal sensors, including camera, LiDAR and millimeter-wave radar, to generate real-time environmental awareness in Fig. 8b. To bridge the gap between simulation and real-world testing, we developed an augmented-reality testing framework. As depicted in Fig. 8c, this system synchronized traffic flows generated by the Simulation of Urban Mobility (SUMO) simulator with the physical test environment, with the full vehicle-in-the-loop testing procedure provided in Supplementary Note 2 and Supplementary Fig. 2. Virtual BVs from SUMO were dynamically projected into the 3D point cloud and camera view in real time, creating

# an augmented perceptionARTICLE IN PRESS scenario where the AV interacted with both physical and

simulated BV entities. The synchronization mechanism, detailed in [11], ensured temporal and spatial consistency between virtual and real components. Specifically, v irtual B Vs generated from SUMO are mapped to AV coordinate system via a synchronization mechanism to ensure spatial alignment. 3D car models of virtual BVs are rendered into AV’s LiDAR and camera data streams, namely synthetic point clouds injected into LiDAR and textured 3D meshes overlaid onto camera video feeds. AV’s standard perception pipeline then processes these augmented sensor data, treating virtual BVs as physical

### ARTICLE IN PRESS

ab Without Activation FunctionWithout Activation Function

1.11.1 0.14 1.2 1.01.0

0.90.9 1.1 0.12 0.80.8

0.71.00.7

uu 0.60.60.10 MM 0.9 0.5Normal Training0.5Normal Training

0.40.4 0.08 0.8 0.30.3

0.20.2 0.7 −530.06 Collision Rate (10)|Jerk|95th (m/s) 0.10.1

0.0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.00.0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 MlMl

cd Without Activation FunctionWithout Activation Function

0.0600 1.11.1 28.2

1.01.00.0575

28.0 0.90.9 0.0550 0.827.80.8

0.0525 0.70.7 27.6

uu 0.60.60.0500 MM 27.4 0.5Normal Training0.5Normal Training 0.0475

0.427.20.4 0.0450 0.30.3 27.0 0.0425 0.20.2 Average Speed (m/s)26.8 Environmental Risk 0.10.1 0.0400

0.0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.00.0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 MlMl

Fig. 7 Sensitivity analysis of the activation function. The combined impact of the lower bound Ml and upper bound Mu of the activation function is evaluated with respect to TV performance in terms of collision rate (a), the 95th percentile absolute jerk (b), average speed (c), and environmental risk (d). Source data are provided as a Source Data file.

# entities,andoutputsARTICLE IN PRESSaunifiedo bjectl istf ormattedi denticallyt ot hatu sedi nthe

simulation. To evaluate the robustness and safety of AV under adversarial conditions, we con- structed challenging scenarios with ABV maneuvers. As illustrated in Fig. 9a, the GA2AD framework shifts the risk profile t oward t he r isky r egion c ompared t o the normal environment. Specifically, t he 5 th p ercentile o f T TC i nt he G A2AD envi- ronment is merely 0.54 s, representing a substantial increase in hazardous exposure, whereas the 5th percentile in the normal environment remains at a safer level of 3.41 s. Furthermore, 34.97% of the recorded TTC values are below 2 s in the GA2AD environment, which is about 58 times higher than the proportion (0.60%) observed in

### ARTICLE IN PRESS

Fig. 8 Vehicle-in-loop field test at the AV test track. a, Illustration of the Heihe testing track, where the red line denotes the AV driving route. b, Illustration of the AV perception scheme, including the ranges and angles of multiple sensors. c, Illustration of the augmented-reality view. Left, simu- lation view, where virtual BVs are generated and controlled by the BV model to interact with the AV. Middle, original and augmented 3D point-cloud views of the AV visualized by ROS, where the augmented BVs are overlaid into the point cloud. Right, comparative front-camera views, including the original scene and the augmented-reality overlay with the synchronized virtual BV. Map data in

# ARTICLE IN PRESS

a are derived from OpenStreetMap. Map data © OpenStreetMap contributors, available under the Open Database License. The simulation visualization in c was generated using Eclipse SUMO.

the normal training environment. This distributional shift at the extreme tails shows that the GA2AD framework produces long-tail hazardous augmented-reality scenarios that occur far more frequently than in typical traffic. Th ese sc enarios pr ovide highly challenging test cases for evaluating AV robustness. Furthermore, the behavioral realism of these adversarial scenarios is supported by the statistical similarity between the prevalence of collision types generated by GA2AD

### ARTICLE IN PRESS

and real-world crash data. By comparing our results with the U.S. National Highway Traffic Safety Administration (NHTSA) Traffic Safety Facts 2023 report [35], as illus- trated in Fig. 9b, we found that the distribution of major conflict c ategories i n the GA2AD environment aligns with U.S. real-world patterns. While direct comparabil- ity between our simulated conflicts i n C hina a nd U .S. r eal-world c rashes i s subject to traffic cu lture di fferences, the pre valence hie rarchy sho ws sim ilarity. For instance, Rear-End and Angle collisions remain the dominant accident modes in both datasets, accounting for the largest proportions of total events. This consistency indicates that the adversarial interactions produced by the BV model, such as abrupt lead-vehicle deceleration or lateral maneuvers, follow a similar prevalence hierarchy to actual traf- fic s afety c hallenges, t hereby e nsuring t he g enerated s cenarios a re b oth c ritical and representative. The normally trained and GA2AD-trained policies were trained using the sim- ulation and training settings described in Methods and were then deployed on the autonomous vehicle for comparative evaluation. We have included quantitative results about the frequency of evasive maneuvers and near-missing events from the field test in Fig. 9c, which provides a comprehensive comparison of the performance of differ- ent GA2AD-trained RL algorithms. A near-missing event is defined as an event where the TV comes dangerously close to a collision but manages to avoid it. Among them, the GA2AD-trained DDPG encountered the lowest frequency of near-missing events, resulting from its highest frequency of evasive maneuvers, which refers to the frequency at which the TV performs evasive actions (deceleration, acceleration, and lane chang- ing) per hour to avoid potential collisions or hazardous situations. A higher frequency of evasive maneuvers also contributes to a lower collision rate of the TV model with GA2AD-trained DDPG. Due to the extreme rarity of naturalistic collisions, collision frequency in field test is estimated using an accelerated virtual-physical fused evaluation framework that explicitly increases the density of GA2AD-generated high-risk interactions. By deliberately inserting the real AV into these GA2AD-generated high-risk scenarios, the proposed testing configuration a mplifies co llision ri sk ex posure wi thin a limited amount of test-track mileage, while preserving realistic vehicle dynamics and closed- loop responses. Formally, the overall virtual-physical fused collision rate is synthesized by com- bining (i) empirically measured conditional collision probabilities obtained from vehicle-in-the-loop field tests under GA2AD-induced adversarial interactions, and (ii) statistically estimated scenario exposure frequencies derived from large-scale mixed-

# ARTICLE IN PRESS−5

traffic si mulations (a pproximately 5.5 × 10 /k m). De tailed de scriptions of th e field test procedures are provided in the Supplementary Note 2. Thus, one kilometer of field t esting u nder t he p roposed a ccelerated configuration provides risk exposure equivalent to approximately 1.8×10km of driving with respect to the GA2AD-defined high-risk adversarial scenarios, thereby enabling effective eval- uation of relative safety performance in these specific challenging conditions. Although it is not a direct measurement of purely real-world naturalistic crash frequency, this virtual-physical fused collision rate reflects t he s afety p erformance a chieved b y the AV during the field test under GA2AD-generated adversarial conditions. As shown in

### ARTICLE IN PRESS

Fig. 9d, the resulting collision rates remain higher in order of magnitude than typical real-world collision rates in China [28], thereby confirming t he G A2AD framework’s ability to actively generate and evaluate long-tail hazardous scenarios. Addition- ally, the GA2AD-trained RL models consistently outperform the normally trained counterparts in terms of virtual-physical fused collision rates as shown in Fig. 9d, demonstrating improved relative safety performance of GA2AD adversarial training under GA2AD-generated adversarial conditions on the physical AV platform. Notably, the normally trained DQN demonstrates improved safety performance compared to other normally trained variants under these conditions. Therefore, we selected the normally trained DQN as the representative baseline to quantify the performance disparity with GA2AD-trained algorithms across other metrics. Figs. 9e-g show the performance of the four algorithms across three metrics: the 95th percentile absolute jerk, average speed, and environmental risk, with additional quantification o f t he d isparity r elative t o t heb aseline ( normally t rained DQN). The field t est r esults p rovide p reliminary e vidence t hat G A2AD-trained models can be successfully deployed in vehicle-in-the-loop adversarial testing environments and achieve lower virtual-physical fused collision rates compared to normally trained referred models, providing empirical evidence of improved relative safety performance under challenging virtual-physical fused adversarial conditions. Among the algorithms evaluated, the DDPG algorithm generally shows improved performance in safety and comfort metrics, with its performance loss in average speed remaining within an acceptable range compared to other algorithms.

### Discussion

Our results demonstrate that the GA2AD framework can increase the robustness and safety of AVs in mixed traffic through ad versarial training. The dynamic interactions between TV and adversarial BVs have been simulated to help the TV model adapting to adversarial scenarios. The activation function edits the MDP and accelerates the training process of the BV model, improving the training efficiency. Th e training process for the TV and BV models is also separated and alternated to dynamically adjust the adversarial intensity for enhancing the TV’s defensive capabilities. The TV model is treated as a black-box in this framework, which facilitates GA2AD’s generalization across the tested models as demonstrated by cross-comparison among variants of TV models. While the GA2AD framework has demonstrated its efficacy in ro bustness, safety,

# ARTICLE IN PRESS

comfort, timing efficiency, ge neralizability an d sc alability, se veral li mitations should be noted. Under the condition of the uncooperative interactions between the TV and BVs, a deep exploration into the game-theoretic equilibria under various traffic con- ditions would provide valuable insights into the long-term stability and evolution of mixed traffic flows. Alt hough such an equ ilibrium ana lysis is beyond the sco pe of the current work due to the inherent limitations of simulation-based experiments, we pro- pose to explore this direction in future research by incorporating real-world data and more advanced modeling techniques to derive and analyze equilibria, which could help predict emergent traffic behaviors and inform strategies for optimizing overall system

### ARTICLE IN PRESS

GA2AD a Normal Environment 35.0%0.6% 0.4

0.2 0.54s3.41s TTC Frequency 0.0 0 1 2 3 4 5 6 Time to collision (s) bcd

Real-world)Normally Trained 6056.0%GA2ADEvasive Maneuver100−5GA2AD-trained Near-Missing (10 41.4%4075 4033.0% 27.4%50 21.5%2 16.4%20Near-Missing Evasive Maneuver25 4.1%Collision Rate 0.2% Percentage of Crashes (%)0000 Angle Rear-End Sideswipe Head-OnSAC TD3 DQN DDPGDQN DDPG TD3 SAC

efg

DQN↓0.06DQN↓2.18DQN↓0.17

DDPG↓0.12DDPG↓1.20DDPG↓0.23

TD3↓0.03BaselineTD3↓0.47BaselineTD3↓0.14Baseline

SAC↓0.11(Normally Trained DQN)SAC↓0.59(Normally Trained DQN)SAC↓0.12(Normally Trained DQN)

0.100 0.125 0.150 0.175 0.200 0.2258 9 10 110.65 0.70 0.75 0.80 0.85 |Jerk|95th (m/s)Average Speed (m/s)Environmental Risk

Fig. 9 Field test results. a, Risk profile u nder t he G A2AD-created a dversarial e nvironment with an elevated risk of near-collisions. b, Prevalence of collision types in GA2AD-generated scenarios compared with real-world NHTSA data. c, Comparative performance evaluation of GA2AD-trained RL-based AV models, including DQN, TD3, DDPG, and SAC, based on the frequency of eva- sive maneuvers and near-missing events. d, Virtual-physical fused collision rates estimated for both GA2AD-trained and normally trained RL models. e–g, Performance comparison between GA2AD- trained models and the normally trained DQN baseline in terms of the 95th percentile absolute jerk (e), average speed (f), and environmental risk (g). Source data are provided as a Source Data file.

safety and efficiency. It is im portant to no te th at th e TT C an dit s in verseus ed in this framework primarily reflect the interaction dynamics and proximity between vehi- cles. Although a higher frequency of low-TTC events indicates increased hazardous exposure, it is not an inherent measure of absolute overall crash risk or severity. For example, an AV system might frequently operate in low-TTC regimes through precise

# maneuvers whileARTICLE IN PRESS maintaining a lower overall crash severity compared to systems with

higher TTC values but poorer severe edge-case handling. Future work will incorpo- rate more diverse metrics, such as potential collision energy or consequence severity indicators, to complement safety assessment. In addition, although the comparison with real-world collision statistics demon- strates a qualitative alignment in the prevalence of major conflict types, the micro-level behavioral realism of the adversarial maneuvers (e.g., precise deceleration rates and lateral trajectories) has not yet been quantitatively validated against naturalistic human driving data. This remains a persistent challenge across the field, as even large- scale naturalistic driving studies (such as the research about SHRP2 project [36])

### ARTICLE IN PRESS

contain very few severe events suitable for such validation. One direction for future work would be to explore the feasibility of combining naturalistic driving study (NDS) trajectories with event data recorder (EDR) information from actual crash databases, although the scarcity of high-severity events continues to present a major obstacle [37]. Additionally, the framework primarily evaluates collision rates and the 95th per- centile absolute jerk within a limited duration or distance, which might not adequately reflect t he l ong-term a daptability a nd s tability o f t he s ystem i n m ore c omplex and heterogeneous traffic sc enarios. It sh ould al so be no ted th at pr e-crash ki nematics in these GA2AD-generated or augmented-reality scenarios may differ fundamentally from those observed in real-world naturalistic crashes, particularly in terms of urgency and criticality [38]. Moreover, although our vehicle-in-the-loop adversarial testing demon- strates clear relative safety gains under the GA2AD-generated scenarios, converting these relative safety gains from virtual-physical testing into real-world safety benefits remains an important direction for future large-scale on-road validation. In this context, future work will focus on addressing the limitations mentioned above by validating the framework in real-world driving environments through software-in-the-loop, hardware-in-the-loop, vehicle-in-the-loop, and augmented reality. Regarding future real-world deployment of autonomous vehicles, the framework will be configured to introduce a safety margin around each vehicle as a safety mechanism. Furthermore, more functional safety mechanisms, i.e., fail-safe, fail-silent, and fail- operational, will be considered in real-world autonomous vehicle deployment in future work. Efforts w ill a lso b e m adet o o ptimizec omputational e fficiency for large-scale heterogeneous traffic ne tworks an d to ex plore ad aptive le arningst rategies, su ch as meta-reinforcement learning, to increase the practicality, applicability and reliability of AVs in the real-world. Moreover, extending the framework to incorporate advanced metrics that balance safety, efficiency, and passenger comfort over longer time horizons will be a priority. The activation function currently employs a hard switch between policies due to SUMO simulator’s limitations regarding discrete action space. How- ever, the underlying structure of our activation function can actually achieve a convex combination of policies. In future work, we plan to implement a convex combination of policies through the proposed activation function by deploying advanced simulation environments with continuous action spaces.

### Methods

Problem formulation

# ARTICLE IN PRESS

This study tackles the issue of adversarial training in multi-agent driving environ- ments by modeling the interaction between the TV agent, referred as α, and the BV agent with the adversarial attack, termed β, which seeks to exploit the TV’s weaknesses. We represent this interaction as a two-player MDP, defined a s M = ⟨S, (Oα, Oβ), (Aα, Aβ), P, (Rα, Rβ), γ⟩, where S denotes the state space; Oαand Oβ are the observation sets for TV and BV, respectively; Aα and Aβ are the action sets; ′′ P is the transition probability, P : S × Aα× Aβ→ S, with Sindicating the probabil- ity distribution over the next states; Rα and Rβ are the reward functions, expressed

### ARTICLE IN PRESS

′ as R : S × Aα × Aβ × S→ R; and γ represents the discount factor that quantifies the diminishing value of future rewards [39]. In the GA2AD training framework, the TV agent and the BV agent are modeled as independent and competitive entities. These agents operate without any telecom- munication, and neither have white-box access to the other’s input states nor share parameter information in their respective weight configurations. As a result, each agent independently develops its own policy, denoted as πα ∈ Πα for the TV agent and πβ ∈ Πβ for the BV agent. To stabilize the training process, this framework alternates the training between these two agents: when the BV agent is being trained, the parameters of the TV agent remain fixed, and vice versa. Such an alternated training setup allows the Markov game, involving two players, to be simplified as a single-player MDP during the phases where one player’s policy remains unchanged. The principal aim for the BV player ∗ during its training phase is to refine its policy πto maximize the cumulative sum of β the discounted rewards, leveraging the fixed strategy of the TV player during TV’s inactive training periods. This can be formulated as follows:

" # ∞ X ∗t(t)(t)(t+1) π= arg maxE(t+1)α(t)(t)γRβ(s, a, s) | s0= s, (1) β s∼P (·|s,a) β πββ (t)(t)t=0 a∼πβ (·|s) β

(t) where actions aβ∼ πβ(·|s) are sampled from the BV agent’s policy, and the resulting (t+1) α(t)(t)α state s∼ P (s, a) follows the transition probability P in the BV training β β β α process, where P is controlled by the policy of the TV model πα. β After the training of policy of the BV agent finished, the BV model serves to stimulate defensive patterns for TV against BVs’ hazardous behaviors introduced to the policy παof the TV. When the BV agent’s strategy effectively creates hazardous cases for the TV (such as collision), the TV model is updated by retraining its weight parameters, while freezing the BV agent in the training environment. The TV agent ∗ optimal policy π, is to maximize the accumulated discounted rewards: α

" # ∞ X ∗t(t)(t)(t+1) πα= arg maxE(t+1)β(t)(t)γRα(s, aα, s) | s0 = s, (2) s∼P (·|s,a) παα (t)(t) a∼πα(·|s)t=0 α

# ARTICLE IN PRESS

(t) where actions aα∼ πα(·|s) are sampled from the TV agent’s policy, and the resulting (t+1) β (t)(t)β state s∼ Pα(s, aα) is determined by the transition probability Pαin TV training process, reflecting the interaction with the environment while considering the adversarial behaviors introduced by the BV agent. In this context, the policies παand πβare the only elements that can be learned. The reward for the TV model is therefore a function of both policies: Rα(πα, πβ). Similarly, the BV model aims to maximize its own reward, Rβ, which is also dependent ∗ ∗ onbothpolicies:Rβ (πα,πβ ).AStackelbergequilibrium(πα ,πβ)forthejointstrategy of the BV and TV is achieved if the following condition holds [40]:

### ARTICLE IN PRESS

∗ infRα(πα, πβ ) ≥ infRα(πα, πβ ), ∀πα ∈ Πα. (3) ∗ πβ ∈V(π) πβ ∈V(πα) α ∗∗ Here, V(πα) = {π∈ Πβ| Rβ(πα, π) ≥ Rβ(πα, πβ), ∀πβ∈ Πβ} represents the β   β best response set of the BV, meaning it includes all policies πβthat maximize the BV’s reward given the TV’s policy πα. Under this condition, the optimal equilibrium reward for this game, denoted as ∗ R, is defined by the following minimax-maximin equality [20]: α

∗ R= minmaxRα(πα, πβ) = maxminRα(πα, πβ). (4) α πβπαπαπβ This GA2AD framework, therefore, enables both the BV and TV agents to explore and exploit strategies in a competitive setting. The independent and adversarial nature of these two agents fosters the development of policies that are robust to various disturbances, which promotes an efficient and stable alternating learning process. Fur- thermore, this interaction-based learning setup captures key aspects of the dynamic and adversarial nature of real-world autonomous driving scenarios, where autonomous vehicles must continuously adapt to the actions of other road users.

Background vehicle model

In this study, we model an adversarial environment for an AV, referred to as the TV, focusing on its interactions with six surrounding BVs. As shown in the top left of the Fig. 1b, we define the set of BVs as follows:

ΩB = {front, left − front, right − front, rear, left − rear, right − rear}. (5)

We propose a BV model to control BVs located at these specific locations relative to the TV. The BV model consists of two parts, namely the RL-based BV model and the rule-based BV model. At each time step, BVs are controlled by the rule-based model by default, which is programmed to follow predefined traffic rules. Unlike other research [41] that directly applies the rule-based AV model to refine a nd constrain decisions of the AV made by the RL-based AV model, this model establishes a stable and normal driving environment that mimics typical human driving patterns, allowing the TV to initially learn basic safe interactions in moderate traffic co nditions. The RL-based BV model is trained on the basis of the rule-based model to select the most suitable ABV candidate b ∈ B to carry out adversarial actions during the training

# processoftheBVmodel.ARTICLE IN PRESSTheRL-basedBVmodeldynamicallyintroducesadversarial

scenarios, enhancing the TV’s ability to handle complex and challenging situations, thereby improving its robustness and safety performance. In detail, the observation space of the RL-based BV model encompasses two main components. First, the TV’s states, including the lateral position (xt), speed (vt), acceleration (at), and heading angle (θt) are considered. Second, the states of the BVs are considered, including the relative distance (∆db), speed (vb), and acceleration (ab) of the BVs. The action space of the RL-based BV model includes two types of actions: the first i s t he s election o f t he A BV c andidate, w hich d etermines t he s pecific ABV to perform adversarial actions; the second involves adversarial maneuvers, namely

### ARTICLE IN PRESS

planning specific adversarial actions for the selected ABV, including braking, throttle, and steering commands. The inverse risk assessment module evaluates the potential risk posed by surround- ing BVs to the TV, and then determines whether adversarial actions should be taken. Specifically, the inputs to the activation function are derived from the proposed inverse risk assessment approach. When the risk of the selected ABV fulfills the conditions for the activation function, this ABV candidate b will actually perform adversarial actions. If not, the selected ABV will perform default behaviors.

Inverse risk assessment

In this paper, to identify the most suitable ABV candidate, we combine two Surrogate Safety Measures (SSMs), namely traditional artificial risk field and TTC to inversely evaluate the safety of the TV by analyzing the risk between the BVs and the TV [42]. The traditional artificial risk field for BVs, as shown in the left part of Fig. 1c, quan- tifies the potential hazardous impact of these BVs in dynamic traffic environments, considering both spatial position and absolute velocity [43]. The risk value reaches its maximum within the BVs’ occupied region, signifying an uncrossable obstacle, and diminishes as the distance from the BVs increases. This risk decay is asymmetric in that a higher BVs’ velocity in the longitudinal direction has a greater influence [44]. In specific, the longitudinal decay factor, ϕx,b(∆x, ∆y, t), represents how the risk diminishes along the BV’s longitudinal axis. It is defined as follows:  . ϕx,b(∆x, t) = μx,b· max|∆x| − Lb, 0(ρx,b· vx,b(t) + 1) , (6)

where ∆x denotes the longitudinal relative position, Lbis the length of the BV, and vx,b(t) represents the vehicle’s longitudinal speed at the time instant t. The parameters μx,band ρx,bcharacterize the intensity of the risk decay. The max function ensures that the decay factor accounts for the vehicle’s physical dimensions, maintaining a maximum risk value within the occupied region. Similarly, the lateral decay factor, ϕy,b(∆x, ∆y, t), quantifies the risk attenuation along the vehicle’s lateral axis. It is expressed as follows:  . ϕy,b(∆y, t) = μy,b · max|∆y| − Wb, 0(ρy,b · vy,b(t) + 1) , (7)

# ARTICLE IN PRESS

where ∆y denotes the lateral relative position, Wb is the width of the BV, and vy,b(t) represents the vehicle’s lateral speed. The parameters μy,b and ρy,b control the lateral risk decay intensity and the effect of the lateral speed, respectively. These directional decay factors above are integrated via the Euclidean norm to compute the combined decay factor: q ϕb(∆x, ∆y, t) =ϕ(∆x, t) + ϕ(∆y, t). (8) x,by,b

### ARTICLE IN PRESS

This combined factor provides an overall measure of the risk decay at a given relative position (∆x, ∆y). However, it overlooks the influence of the behavior of TV in specific environments. Thus, we introduce the TTC to the traditional risk field, which results in the generation of a hybrid risk field [7]. The formulas of the TTC on different axes are defined as follows: ( ∆x , if ∆x∆v> 0 ∆vx x TTCx=, (9) +∞, otherwise ( ∆y , if ∆y∆v > 0 ∆vy y TTCy=, (10) +∞, otherwise where ∆vx, and ∆vy represent the longitudinal and lateral relative velocities between the BV and TV, respectively. The introduction of TTC into the traditional risk field enables the incorporation of relative velocity effects, such that higher relative speeds intensify the perceived risk. The hybrid risk field is characterized by continuity, directionality with distinct decay rates along longitudinal and lateral directions, and sensitivity to relative velocity, providing a dynamic representation of vehicle interactions as shown in the middle part of Fig. 1c. The hybrid risk field function for the BVs is then defined as:

− − TTCTTCy (2 − ex − e) ηb = , (11) (ϕb(∆x, ∆y, t) + 1)

where ηbrepresents the risk field value at position (∆x, ∆y) around the BVs at the time insant t with a relative velocity (∆vx, ∆vy). This formulation ensures that the risk is maximal within the occupied region of the BV and decreases smoothly to near zero as the distance from the BV increases. The constant 1 in the denominator guarantees that the risk function remains valid even when the speed of the BVs is zero. After the hybrid risk field value is obtained, it is used to measure the risk level via the risk function deterministically. However, due to the uncertainties from the dynamic traffic environment, the deterministic method may lead to bias in safety evaluation [45]. So we utilize a probabilistic risk assessment framework for evaluating the risk associated with BVs. The risk levels are hierarchically divided into three

# categories corresponding to high, medium, and low risk levels. The risk level is definedARTICLE IN PRESS

as: def τ ∈ Ω = {dangerous, attentive, safe} = {D, A, S}, (12)

### ARTICLE IN PRESS

where Ω denotes the set of risk levels. The likelihood functions P (ηb|τb) are defined based on the distribution of safety metrics ηb, which are defined as follows:  (η−η) bD − 2σ eD , if η ≤ η P (ηb|τb= D) =bD,  1, otherwise  (η−η) bD − 2 2σ eD , if ηb> ηD  (η−ηS) b P (ηb|τb= A) =− ,(13) 2σ eS , if ηb< ηS    1, otherwise  (η−η) bS − 2σ eS , if η ≥ η P (ηb|τb= S) =bS,  1, otherwise

where ηb denotes the hybrid risk field values from the BVs to the TV, which serve as the critical metric in risk assessment. Based on our extensive experiments and existing literature such as [44] and [46], the hyper-parameters ηD and ηS are predefined for different risk thresholds, which satisfies ηD > ηS. Other hyper-parameters, such as σS and σD, are strategically utilized to ensure the smooth transition of risk levels across varying distributions, enhancing the sensitivity and reliability of the risk assessment in different traffic scenarios. The term P (ηb|τb), denotes the likelihood of observing the safety metric ηb under the assumption that the risk level is τb. The right part of Fig. 1c shows a graphical illustration of the formula presented in Eq. 13, facilitating a better understanding of the risk assessment dynamics as influenced by these hyper- parameters above. These hyper-parameters are chosen based on the prior distribution of risk levels, ensuring that the risk distributions are appropriately smoothed for a balanced and continuous representation of varying risk scenarios. Further details on the rationale and methodology behind the determination of these hyper-parameters are described in [46–48]. Furthermore, the posterior probability of the risk level τb is computed via Bayesian inference, which is mathematically expressed as follows:

P (ηb|τb) · P (τb) P (τb|ηb) = P. (14) P (τ) · P (η|τ) τb∈Ω bbb

# ARTICLE IN PRESS

In this formulation, P (τb|ηb) represents the posterior probability of risk level τb given a specific safety metric ηb. Additionally, P (τb) signifies the prior probability of the risk level τb. For simplifi- cation, a uniform prior probability distribution is assumed across different risk levels, P subject to the normalization condition P (τb) = 1. Therefore, in practice, the τb∈Ω Eq. 14 is transformed as follows:

P (ηb|τb) P (τb|ηb) ∝ P. (15) P (η|τ) τb∈Ω bb

### ARTICLE IN PRESS

To evaluate the holistic risk level of the surrounding environment of the TV, we con- sider the integrated risk levels of surrounding BVs. In detail, a probability distribution of the risk level for the surrounding environment is determined by the probability dis- tribution of the risk level for the most imminent risk from the BVs. For the surrounding environment, the probability distribution of the risk level is defined as follows: Y P (τenv = D) = 1 − (1 − P (τb = D|ηb)) , (16) b∈B Y P (τenv= S) = P (τb= S|ηb) , (17) b∈B

P (τenv = A) = 1 − P (τenv = S) − P (τenv = D), (18) where P (τenv = D), P (τenv = A), and P (τenv = S) represent the probabilities that the surrounding environment is inferred to be dangerous, attentive, and safe, respec- tively. The probabilities of the risk level of the BVs are denoted by P (τb = D|ηb), P (τb = A|ηb), and P (τb = S|ηb), respectively. To determine the BV policy that maximizes the expected risk, the outputs from the inverse risk assessment help the RL-based BV model enhance the effectiveness of its adversarial behavior modeling. However, the risk assessment output, P (τ |η), is inherently discontinuous, posing challenges for its direct application in continuous inference in RL methods. To address this limitation, a continuous risk parameter ϵ is derived from the posterior probability P (τ |η) by incorporating the discrete risk levels τ . Given that the risk categories D, A, and S in Eq. 12 cannot be directly used for expectation calculation, a scoring function Sc(τ ) is introduced to map the risk levels to numerical scores, assigning values of 2, 1, and 0 to D, A, and S, respectively. The continuous risk expectation ϵ is formulated as follows: X ϵ = E(τ ) = Sc(τ ) · P (τ |η), (19) τ ∈Ω

where τ represents discrete risk levels, while ϵ is a continuous measure of risk that facilitates its integration into the continuous learning and decision-making processes. The expected risk of the BV, denoted as ϵb, and the expected risk of the surround- ing environment, denoted as ϵenv, can be obtained based on P (τb|η) and P (τenv |η), respectively. To provide an intuitive physical interpretation of the computed results, we further

# ARTICLE IN PRESS

analyze the relationship between the proposed environmental risk ϵenv and the safety metric TTC. Specifically, under safety-critical conditions, ϵenv can be asymptotically simplified to be inversely proportional to TTC:

ϵenv ∝ , (20) TTCb∗

where the TTCb∗ denotes the smallest TTC among all BVs to the TV. This rela- tionship reflects t hat s horter T TC v aluei ndicates h igher e nvironmental r isk. The detailed derivation of this formula is provided in the Supplementary Note 3. Note that

### ARTICLE IN PRESS

TTC primarily characterizes vehicle proximity and interaction dynamics; it doesn’t directly measure crash severity or absolute crash risk. Nevertheless, under the con- sidered adversarial scenarios, a smaller TTC serves as a useful indicator of increased hazard exposure.

Activation function

Ensuring an appropriate balance between conservativeness and aggressiveness in the BV model β presents a considerable challenge. Excessive passivity during certain time steps can result in overly conservative scenarios, limiting the generation of positive samples required for effective adversarial training. Conversely, an overly aggressive BV model may severely disrupt the learning process of the TV model α, as it may fail to react adequately to overly aggressive adversarial maneuvers [49]. To address this challenge, an activation function is proposed to regulate the influ- ence of adversarial actions, ensuring BV’s impact remains benificial for training while avoiding excessive aggression. The activation function evaluates the suitability of the ABV candidate based on its expected risk ϵb and the surrounding environmental risk ϵenv. The activation function f (ϵb, ϵenv) is defined as follows: ( ϵenv 1, if Ml< < Mu −k(ϵ−ϵenv ) 1+eb f (ϵb, ϵenv) =, (21) 0, otherwise

where k is a positive constant that governs the steepness of the function. Mland Mu are the lower and upper thresholds respectively. When the ABV candidate’s expected risk ϵb<< ϵenv, the exponential term becomes dominant, driving f (ϵb, ϵenv) close to 0, which implies a relatively low-risk scenario, indicating the candidate’s inadequacy for adversarial maneuvers. Conversely, when ϵb> ϵenv, the exponential term dimin- ishes, causing f (ϵb, ϵenv) to approach 1, thereby amplifying the adversarial influence. Moreover, if ϵenvis excessively high, this indicates that the TV’s surrounding environ- ment is already hazardous, and selecting such a candidate for adversarial actions may directly lead to a collision, which is also undesirable [50]. RB The BV policy πβ, which consists of a rule-based policy πand a RL-based β RL policy πβ, leverages the activation function f (ϵb, ϵenv) to modulate the adversarial behavior of the ABV candidate in a manner that is consistent with the surrounding risk levels. Building on the concept of balancing passivity and aggressiveness, the activation RBRL function determines whether the ABV candidate should follow πβor πβas defined

# ARTICLE IN PRESS

in Box 1. This decision is driven by the relative risk levels, ensuring that adversarial maneuvers are applied only when appropriate. Specifically, i f t he a ctivation function value exceeds a predefined t hreshold M u o r l ies b elow Ml, t he B V a dopts a passive rule-based approach, avoiding unnecessary interventions. By dynamically adapting to risk levels, the algorithm ensures that adversarial actions are impactful but not overly disruptive, consistent with the goal of creating diverse driving scenarios to enhance the robustness of the TV policy. By incorporating this activation function into the GA2AD framework, we balance the aggressiveness of adversarial actions. This ensures that the adversarial behaviors

### ARTICLE IN PRESS

are strong enough to challenge the TV and promote learning, yet not so aggressive that they create unrealistic or unmanageable scenarios. This approach supports the TV’s learning process in an adversarial environment, encouraging adaptive and resilient AV behaviors.

Box 1 | BV policy πβwith activation function

1: Input: Observation oβ 0RB 2: a= π(oβ ) β β 1RL 3: (b, a) = π(oβ) β β 4: Obtain the expected risk ϵband ϵenv 5: a← (1 − f (ϵb, ϵenv))a+ f (ϵb, ϵenv)a β β β 6: aβ ← (b, a) β 7: Output: aβ

Adaptive switch module

In the GA2AD framework, a mechanism termed the switch indicator CRis integrated to adaptively adjust the training process between the TV and the BV. This switch is governed by a threshold value (H), which is determined by our extensive experiments with an automatic hyperparameter optimization software framework Optuna [51]. The training target shifts towards the TV when CR> H, and to the BV when CR≤ H. The adoption of this mechanism mitigates instability issues inherent in multi-agent frameworks by converting the training setup into a more stable single-agent context. This process not only enhances the adaptability and learning efficiency throughout different stages but also maintains the universality of the training, aiming to ensure safety and robustness in various driving scenarios. As described in Box 2, CR= is employed as an indicator, where Ccrepresents C c the collision episode interval between two consecutive collisions of the TV under the condition of f (ϵb, ϵenv) = 1 during training. A small Cc(equivalently, a large CR) indicates high collision frequency, prompting the GA2AD to focus on TV training to enhance robustness. A large Cc(a small CR) indicates low collision frequency, indi- cating that the GA2AD to enhance the adversarial intensity of the BV. Consequently, using CRas an indicator allows for the adaptive and dynamic adjustment of the train- ing strategies for the TV and the BV, ensuring that the TV is not overly subjected

# ARTICLE IN PRESS

to adversarial conditions. The design of CRnot only enables the training process to flexibly r espond t o c hanging d riving c onditions, b ut a lso e xhibits s calability, making it applicable to various training scenarios and TV models. The adaptive switch mod- ule can gradually adjust the adversarial intensity of the ABV to make the changes in adversarial intensity smoother, enhancing the safety and robustness of the AV system under diverse adversarial conditions.

### ARTICLE IN PRESS

Box 2 | Generalized adaptive adversarial training process

T VBV 1: Initialize learning parameters θfor παand θfor πβwith TV memory 0  0 Mαand BV memory Mβ 2: Initialize the environment ENV to obtain initial states and observations oα and oβ 3: Initialize the switch indicator CRand switch threshold H, satisfying CR> H 4: Set collision episode interval Cc= 1 5: for i = 1 to Nepochdo 6: while t < T do 7: aα= πα(oα) 8: aβ= πβ(oβ) ′′ 9: rβ, rα, o, o= ENV(aα, aβ) αβ 10: if CR> H then ′ 11: Append (rα, sα, o, aα) to Mα α 12: Update πα 13: else 14: if f (ϵb, ϵenv) = 1 then ′ 15: Append (rβ, sβ, o, aβ) to Mβ β 16: Update πβ 17: end if 18: end if 19: if the target vehicle collides and f (ϵb, ϵenv) = 1 then 20: CR= 1/Cc 21: Cc= 0 22: break 23: end if 24: end while 25: Cc= Cc+ 1 26: end for 27: Output πα, πβ

BV reward function

# In this paper, the reward function for the RL-based BV model includes three com-ARTICLE IN PRESS

ponents: the collision function, the risk function, and the action penalty. The BV model is incentivized to generate effective adversarial strategies during TV training and enhance the TV’s ability to handle complex and hazardous situations.

R = w1· Rcollision+ w2· Rrisk+ w3· Raction, (22) ( 1, if the TV collides and f (ϵb, ϵenv) = 1 Rcollision =, (23) 0, otherwise

### ARTICLE IN PRESS

Rrisk = ϵenv, (24) ( RLRB −1, if π(oβ) = π(oβ) β  β Raction=. (25) 0, otherwise The collision function Rcollision rewards the RL-based BV model when a colli- sion between the TV and any other BV occurs, for rewarding adversarial attacks to train the TV how to avoid collisions. Crucially, this reward is only triggered when f (ϵb, ϵenv) = 1, signifying that the collision is a direct or indirect consequence of the ABV’s adversarial maneuvers. The risk function Rrisk assesses the overall environmen- tal risk associated with BVs’ actions, where ϵenv represents the level of environmental risk linked to BVs’ behavior, encouraging the RL-based BV model to undertake actions that increase holistic environmental risk, thereby forcing the TV to make safer deci- sions in higher-risk environments. The action penalty Raction is applied if the RL-based BV’s action is the same as that of the rule-based BV model, promoting the RL-based BV model to generate strategies different from conventional rules, adding diversity and adversarial challenge to the TV training.

Evaluation metrics

Improving the safety performance of the TV model is the primary goal of the GA2AD framework, considering the trade-off on efficiency and comfort (i.e., multi-objective optimization with safety as the primary concern). Four metrics, namely, the collision rate, environmental risk, average speed and the 95th percentile absolute jerk, are used to evaluate the performance of the TV model on robustness, which is defined as maintaining safe, stable, and efficient driving under adversarial conditions. The safety metrics like collision rate and environmental risk are inspired by ISO 26262 [52] and ISO 21448 [53] standards, which emphasize the importance of mini- mizing hazard exposure. While direct measurement of injury severity is beyond the scope of our study, reducing collision frequency and environmental risk serves as a foundational step toward minimizing hazard exposure and enhancing AV robustness. The effectiveness of the proposed approach in improving the safety performance of AVs is evaluated via the collision rate, which quantifies the frequency of collisions per kilometer traveled, serves as an indicator of TV safety [54]. Specifically, it is calculated by dividing the total number of collisions by the total distance traveled during the evaluation period. A lower collision rate corresponds to better safety performance and

# ARTICLE IN PRESS

greater robustness to potential disturbances or adversarial influences. The formula is given by: Total Number of Collisions Collision Rate = , (26) Total Distance Traveled where a collision is counted when physical boundaries of the TV and any BV overlap. This definition o f a c ollision o ffers tw o ke y be nefits: it cre ates hig h-risk sce narios to stress-test the TV’s robustness by treating all collisions with the TV as critical safety events to be avoided, and it prevents overfitting t o s pecific fa ultat tribution ru les by not distinguishing between ABV-induced and normal BV-induced collisions, thereby

### ARTICLE IN PRESS

forcing the TV to develop generalized defensive strategies in a dynamic and challenging adversarial environment. The environmental risk metric assesses the TV’s exposure to hazards by consid- ering the dynamic states of surrounding BVs, providing an effective pre-crash safety assessment that overcomes limitations of TTC in capturing multi-vehicle interactions and uncertainties. The definition of the environmental risk is given via Eq. (19) in Methods. The average speed measures the TV’s driving efficiency. Excessively low speeds can disrupt traffic flow and cause congestion. Maintaining a reasonable average speed keeps the AV efficient. The formula is:

NPN X 1(vi× ∆t)Total Distance Traveled i=1 Average Speed = vi == , (27) NN × ∆t Total Time Duration i=1

th where viis the speed at the itime step and N is the total number of time steps, and ∆t is the duration of each time step. Jerk reflects sudden acceleration or deceleration that may lead to passenger dis- comfort or secondary accidents, thus reflecting ride smoothness and indirectly affecting safety. It has been widely used in existing research (e.g. [19, 25]) as a key indicator of ride quality. In this study, the 95th percentile absolute jerk is used to evaluate driv- ing comfort, as it focuses on the highest 5% of extreme jerk values that most greatly impact passenger comfort. By utilizing the 95th percentile, the metric becomes more sensitive to rare but problematic maneuvers that might otherwise be obscured in large datasets. The formula for the 95th percentile absolute jerk is: !  N ai+1 − ai |Jerk|95th = Percentile, 95, (28) ∆t i=1 N N where Percentile({xi}, p) denotes the p-th percentile of the set {xi}; ai is the i=1i=1 th acceleration at the itime step; ∆t is the time step between consecutive samples; and N is the total number of time steps.

Simulation experimental setup

To evaluate the proposed methodology, we constructed an urban traffic scenario using

# the SUMO simulationARTICLE IN PRESS platform based on real-world geographic data. The scenario fea-

tures a 3.2-kilometer mixed-geometry roadway with both straight and curved sections, four standard lanes, and three signalized intersections. A speed range of [0, 35] m/s was implemented to simulate high-speed traffic conditions. Vehicle maneuvers were defined in a 9-dimensional discretized action space, including left and right lane changes and seven discrete longitudinal acceleration values in [−4, 2] m/s, with a resolution of 1 m/s. The BVs’ default maneuvers were generated by a rule-based model incorpo- rating the Intelligent Driver Model (IDM) [55] and the Minimizing Overall Braking Induced by Lane Changes (MOBIL) model [56], with calibrated parameters for acceler- ation, desired speed, and lane-changing behavior to simulate human driving patterns.

### ARTICLE IN PRESS

An ABV was selected by an RL-based model from a 6-dimensional vehicle candidate space to perform adversarial maneuvers, which can capture the randomness and het- erogeneity of human driving behaviors and especially mimic extreme or unpredictable human driving behaviors, through diverse and dynamic adversarial strategies. The TV model, represented by a decision-making module, incorporated an RL algorithm with a reward function emphasizing safety, efficiency, and stable driving behavior. The TV model’s inputs included a 22-dimensional observation space comprising states of the TV and surrounding BVs. To consider behavioral diversity, heterogeneous algorithmic structures are employed for the TV and BV. Specifically, the TV model is initially controlled by a DQN algorithm [57], a classic off-policy and value-based reinforcement learning method that serves as a baseline for comparisons with other RL-driven TV variants. The RL-based BV model is trained using the Proximal Policy Optimization (PPO) algorithm with key hyperparameters configured to balance learning efficiency and adaptability [58]. More details and a reproducible experimental setup can be found in Supplementary Note 1 and Supplementary Tables 1–3.

### Data Availability

Source data are provided with this paper. Source data underlying the main figures and supplementary figures are provided with this paper as a Source Data file. The code used to reproduce the analyses and figures in this study has been deposited in Zenodo under DOI: 10.5281/zenodo.20590737. The OpenStreetMap-derived map and road-network data used for the geographic map panels are publicly available from OpenStreetMap. The SUMO simulation network and configuration files used in this study are included in the deposited materials. The NHTSA traffic crash statistics used for comparison in Fig. 9b are publicly available from the National Highway Traffic Safety Administration. Raw vehicle-in-loop sensor streams and field-test recordings are not publicly released because they contain test-site operational information and high- volume sensor data; the processed data necessary to interpret, verify and reproduce the results are provided in the Source Data file.

### Code Availability

Our complete code, including the generalized adaptive adversarial training frame- work (GA2AD), environment setup instructions, and scripts for result evaluation

# ARTICLE IN PRESS

and testing, has been made available at Zenodo (https://doi.org/10.5281/zenodo.
20590737) [59].

### References

[1] Rahman, M. H., Abdel-Aty, M. & Wu, Y. A multi-vehicle communication sys- tem to assess the safety and mobility of connected and automated vehicles. Transportation Research Part C: Emerging Technologies 124, 102887 (2021).

### ARTICLE IN PRESS

[2] Nyholm, S. & Smids, J. Automated cars meet human drivers: responsible human- robot coordination and the ethics of mixed traffic. Ethics Inf. Technol. 22, 335– 344 (2020).

[3] Atakishiyev, S., Salameh, M., Yao, H. & Goebel, R. Explainable artificial intel- ligence for autonomous driving: A comprehensive overview and field guide for future research directions. IEEE Access 12, 101603–101625 (2024).

[4] Dai, S., Bae, S. & Isele, D. Game theoretic decision making by actively learning human intentions applied on autonomous driving. arXiv preprint (2023). Preprint at https://arxiv.org/abs/2301.09178.

[5] Toghi, B., Valiente, R., Sadigh, D., Pedarsani, R. & Fallah, Y. P. Social coor- dination and altruism in autonomous driving. IEEE Trans. Intell. Transp. Syst. 23, 24791–24804 (2022).

[6] Wu, J., Huang, Z. & Lv, C. Uncertainty-aware model-based reinforcement learn- ing: Methodology and application in autonomous driving. IEEE Trans. Intell. Veh. 8, 194–203 (2023).

[7] Xu, C., Zhao, W. & Wang, C. An integrated threat assessment algorithm for decision-making of autonomous driving vehicles. IEEE Trans. Intell. Transp. Syst. 21, 2510–2521 (2020).

[8] Liang, C., Ghazel, M., Zheng, W. & Chen, W. Dynamic cumulative human-like brake control modeling for autonomous vehicle collision analysis. IEEE Trans. Veh. Technol. 74, 3976–3990 (2025).

[9] Xia, X. et al. An automated driving systems data acquisition and analytics platform. Transportation Research Part C: Emerging Technologies 151, 104120 (2023).

[10] Liu, M. et al. Potential game-based decision-making for autonomous driving. IEEE Trans. Intell. Transp. Syst. 24, 8014–8027 (2023).

[11] Feng, S. et al. Dense reinforcement learning for safety validation of autonomous vehicles. Nature 615, 620–627 (2023).

# ARTICLE IN PRESS

[12] Ghaffari Laleh, N. et al. Adversarial attacks and adversarial robustness in computational pathology. Nat. Commun. 13, 5711 (2022).

[13] Veerabadran, V. et al. Subtle adversarial image manipulations influence both human and machine perception. Nat. Commun. 14, 4933 (2023).

[14] Lammie, C., B¨uchel, J., Vasilopoulos, A., Le Gallo, M. & Sebastian, A. The inherent adversarial robustness of analog in-memory computing. Nat. Commun. 16, 1756 (2025).

### ARTICLE IN PRESS

[15] Qayyum, A., Usama, M., Qadir, J. & Al-Fuqaha, A. Securing connected & autonomous vehicles: Challenges posed by adversarial machine learning and the way forward. IEEE Commun. Surv. Tutorials 22, 998–1026 (2020).

[16] Mo, S., Pei, X. & Wu, C. Safe reinforcement learning for autonomous vehicle using Monte Carlo Tree Search. IEEE Trans. Intell. Transp. Syst. 23, 6766–6773 (2022).

[17] Teng, S. et al. Motion planning for autonomous driving: The state of the art and future perspectives. IEEE Trans. Intell. Veh. 8, 3692–3711 (2023).

[18] Chahe, A., Wang, C., Jeyapratap, A., Xu, K. & Zhou, L. Dynamic adversarial attacks on autonomous driving systems. arXiv preprint (2024). Preprint at https://arxiv.org/abs/2312.06701.

[19] Liang, C., Ghazel, M., Xie, C., Zheng, W. & Chen, W. A dynamic synchronous interactive functional validation approach for electric vehicles. IEEE Trans. Intell. Veh. (2025). https://doi.org/10.1109/TIV.2024.3393559.

[20] Pinto, L., Davidson, J., Sukthankar, R. & Gupta, A. Robust adversarial rein- forcement learning. arXiv preprint (2017). Preprint at https://arxiv.org/abs/ 1703.02702.

[21] Zhang, H., Chen, H., Boning, D. & Hsieh, C.-J. Robust reinforcement learn- ing on state observations with learned optimal adversary. arXiv preprint arXiv:2101.08452 (2021). Preprint at https://arxiv.org/abs/2101.08452.

[22] Behzadan, V. & Munir, A. Adversarial reinforcement learning framework for benchmarking collision avoidance mechanisms in autonomous vehicles. IEEE Intell. Transp. Syst. Mag. 13, 236–241 (2021).

[23] Guo, J., Kurup, U. & Shah, M. Is it safe to drive? An overview of factors, metrics, and datasets for driveability assessment in autonomous driving. IEEE Trans. Intell. Transp. Syst. 21, 3135–3151 (2020).

[24] Teng, S. et al. Hierarchical interpretable imitation learning for end-to-end autonomous driving. IEEE Trans. Intell. Veh. 8, 673–683 (2023).

# ARTICLE IN PRESS

[25] Liang, C., Ghazel, M., Ci, Y. & Zheng, W. Analyzing rear-end collision risk relevant to autonomous vehicles by using a humanlike brake model. Journal of Transportation Engineering Part A: Systems 150, 115604 (2024).

[26] Rashid, T. et al. QMIX: Monotonic value function factorisation for deep multi- agent reinforcement learning. arXiv preprint (2018). Preprint at https://arxiv. org/abs/1803.11485.

### ARTICLE IN PRESS

[27] Huh, D. & Mohapatra, P. Multi-agent reinforcement learning: A comprehensive survey. arXiv preprint (2023). Preprint at https://arxiv.org/abs/2312.10256.

[28] UNECE. Global technical regulation on automated driving system (ads). https: //unece.org/sites/default/files/2024-10/GRVA-WS03-05e.pdf (2024). Online; accessed 29-March-2025.

[29] Fujimoto, S., van Hoof, H. & Meger, D. Addressing function approximation error in actor-critic methods. arXiv Preprint (2018). Preprint at https://arxiv.org/ abs/1802.09477.

[30] Haarnoja, T., Zhou, A., Abbeel, P. & Levine, S. Soft actor-critic: Off-policy maximum entropy deep reinforcement learning with a stochastic actor. arxiv Preprint (2018). Preprint at https://arxiv.org/abs/1801.01290.

[31] Lillicrap, T. P. et al. Continuous control with deep reinforcement learning. arXiv Preprint (2015). Preprint at https://arxiv.org/abs/1509.02971.

[32] Silver, D. et al. Mastering the game of Go without human knowledge. Nature 550, 354–359 (2017).

[33] Feng, S. et al. Testing scenario library generation for connected and automated vehicles, part II: Case studies. IEEE Trans. Intell. Transp. Syst. 22, 5635–5647 (2021).

[34] Macenski, S., Foote, T., Gerkey, B., Lalancette, C. & Woodall, W. Robot Oper- ating System 2: Design, architecture, and uses in the wild. Sci. Rob. 7, eabm6074 (2022).

[35] National Center for Statistics and Analysis. Traffic safety facts 2023: A compila- tion of motor vehicle traffic crash data. Tech. Rep. DOT HS 813 738, National Highway Traffic Safety Administration (2025). URL https://crashstats.nhtsa.dot. gov/Api/Public/ViewPublication/813738.

[36] Dingus, T. A. et al. Driver crash risk factors and prevalence evaluation using naturalistic driving data. PNAS 113, 2636–2641 (2016).

[37] Chen, R. J., Tatem, W. M. & Gabler, H. C. Event data recorders (EDRs) duration

# ARTICLE IN PRESS

study. Tech. Rep., Virginia Tech Transportation Institute / National Highway Traffic Safety Administration (2017).

[38] Olleja, P., B¨argman, J. & Lubbe, N. Can non-crash naturalistic driving data be an alternative to crash data for use in virtual assessment of the safety performance of automated emergency braking systems? J. Saf. Res. 83, 139–151 (2022).

[39] He, K., Doshi, P. & Banerjee, B. Modeling and reinforcement learning in partially observable many-agent systems. Auton. Agents Multi-Agent Syst. 38, 12 (2024).

### ARTICLE IN PRESS

[40] Huang, P., Xu, M., Fang, F. & Zhao, D. Robust reinforcement learning as a stackelberg game via adaptively-regularized adversarial training. arXiv preprint (2022). Preprint at https://arxiv.org/abs/2202.09514.

[41] Zeng, X. et al. Target-oriented maneuver decision for autonomous vehicle: A rule-aided reinforcement learning framework. Proceedings of the 32nd ACM International Conference on Information and Knowledge Management 3124–3133 (2023).

[42] Liu, M., Wan, Y., Lewis, F. L., Nageshrao, S. & Filev, D. A three-level game- theoretic decision-making framework for autonomous vehicles. IEEE Trans. Intell. Transp. Syst. 23, 20298–20308 (2022).

[43] Cheng, S., Wang, Z., Yang, B. & Nakano, K. Convolutional neural network- based lane-change strategy via motion image representation for automated and connected vehicles. IEEE Trans. Neural Networks Learn. Syst. 35, 12953–12964 (2024).

[44] Tan, H., Lu, G. & Liu, M. Risk field model of driving and its application in modeling car-following behavior. IEEE Trans. Intell. Transp. Syst. 23, 11605– 11620 (2022).

[45] Sankar, G. S. & Han, K. Adaptive robust game-theoretic decision making strategy for autonomous vehicles in highway. IEEE Trans. Veh. Technol. 69, 14484–14493 (2020).

[46] Noh, S. & An, K. Reliable, robust, and comprehensive risk assessment framework for urban autonomous driving. J. Comput. Des. Eng. 9, 1680–1698 (2022).

[47] Li, G. et al. Lane change strategies for autonomous vehicles: a deep reinforcement learning approach based on Transformer. IEEE Trans. Intell. Veh. 8, 2197–2211 (2023).

[48] Li, G. et al. Risk assessment based collision avoidance decision-making for autonomous vehicles in multi-scenarios. Transportation Research Part C: Emerg- ing Technologies 122, 102820 (2021).

[49] Geary, J., Gouk, H. & Ramamoorthy, S. Active altruism learning and information

# ARTICLE IN PRESS

sufficiency for autonomous driving. arXiv preprint (2021). Preprint at https: //arxiv.org/abs/2110.04580.

[50] Yang, K. et al. Towards robust decision-making for autonomous driving on highway. IEEE Trans. Veh. Technol. 72, 11251–11263 (2023).

[51] Akiba, T., Sano, S., Yanase, T., Ohta, T. & Koyama, M. Optuna: A next-generation hyperparameter optimization framework. ACM Trans. Knowl. Discovery Data 13, 1–26 (2019).

### ARTICLE IN PRESS

[52] International Organization for Standardization (ISO). Road vehicles–Functional safety. ISO 26262 (E) (2018).

[53] International Organization for Standardization (ISO). Road vehicles–Safety of the intended functionality (SOTIF). ISO 21448 (E) (2022).

[54] Goodall, N. J. Comparison of automated vehicle struck-from-behind crash rates with national rates using naturalistic data. Accid. Anal. Prev. 154, 106056 (2021).

[55] Treiber, M., Hennecke, A. & Helbing, D. Congested traffic states in empirical observations and microscopic simulations. Phys. Rev. E: Stat. Phys. Plasmas Fluids Relat. Interdiscip. Top. 62, 1805–1824 (2000).

[56] Kesting, A., Treiber, M. & Helbing, D. General lane-changing model mobil for car-following models. Transp. Res. Rec. 1999, 86–94 (2007).

[57] Sivayazi, K. & Mannayee, G. Modeling and simulation of a double DQN algorithm for dynamic obstacle avoidance in autonomous vehicle navigation. e-Prime - Advances in Electrical Engineering, Electronics and Energy 8, 100581 (2024).

[58] Wu, Y., Liao, S., Liu, X., Li, Z. & Lu, R. Deep reinforcement learning on autonomous driving policy with auxiliary critic network. IEEE Trans. Neural Networks Learn. Syst. 34, 3680–3690 (2023).

[59] Xu, H. et al. GA2AD: A generalized adaptive adversarial training framework considering surrounding hybrid risk field for autonomous driving (2026). URL https://doi.org/10.5281/zenodo.20590737.

### Acknowledgements

The authors thank the Heihe Autonomous Driving Test Site, China for provid- ing access to the autonomous vehicle test track and for supporting the field-testing experiments.

### Funding Statement

Y.C. discloses support for the research of this work from the National Key R&D Pro-

# gramofChinaARTICLE IN PRESS(GrantNo.2023YFB2603500)andtheHeilongjiangProvincialNatural

Science Foundation of China (Grant No. LH2023E055). C.L. discloses support for the research of this work from the National Natural Science Foundation of China (Grant No. 52402493) and the Heilongjiang Provincial Natural Science Foundation of China (Grant No. LH2024E059). L.W. discloses support for the research of this work from the Program for Young Talents of Basic Research in Universities of Heilongjiang Province, China (Grant No. YQJH2023146), the Fundamental Research Funds for Heilongjiang Provincial Universities, China (Grant No. 2023GJ05), and the Heilongjiang Provincial Natural Science Foundation of China (Grant No. PL2025E077). X.C. discloses sup- port for the research of this work from the National Natural Science Foundation of

### ARTICLE IN PRESS

China (Grant No. 72525009 and No. 72431009). H.X., Y.L., M.G. and L.F. declare no relevant funding.

### Author Contributions Statement

Y.C. and H.X. conceived the study and led the research. H.X. and Y.L. developed the algorithms, implemented the simulation experiments and processed the data. H.X. and C.L. refined t he m ethodological d esign, p erformed t he v isualization a nd drafted the manuscript. M.G., L.F., L.W. and X.C. reviewed and edited the manuscript. Y.C. supervised the project and coordinated the overall organization of the manuscript.

### Competing Interests Statement

Authors declare no competing interests.

# ARTICLE IN PRESS