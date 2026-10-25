-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1
-- Généré le : dim. 25 oct. 2026 à 14:10
-- Version du serveur : 10.4.32-MariaDB
-- Version de PHP : 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `ecoteams_db`
--

-- --------------------------------------------------------

--
-- Structure de la table `accounts_role`
--

CREATE TABLE `accounts_role` (
  `id` bigint(20) NOT NULL,
  `description` longtext NOT NULL,
  `is_system` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `group_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `accounts_role`
--

INSERT INTO `accounts_role` (`id`, `description`, `is_system`, `created_at`, `updated_at`, `group_id`) VALUES
(1, 'Rôle attribué automatiquement à chaque nouvel inscrit.', 1, '2026-10-24 20:32:24.095956', '2026-10-24 20:32:24.095976', 1),
(2, 'Rôle de démonstration : modère les actions, valide défis et événements, consulte les rapports.', 0, '2026-10-24 20:32:42.382655', '2026-10-24 20:32:42.382705', 2);

-- --------------------------------------------------------

--
-- Structure de la table `accounts_user`
--

CREATE TABLE `accounts_user` (
  `id` bigint(20) NOT NULL,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `email` varchar(254) NOT NULL,
  `organization_type` varchar(20) NOT NULL,
  `organization` varchar(120) NOT NULL,
  `city` varchar(80) NOT NULL,
  `bio` longtext NOT NULL,
  `favorite_category` varchar(20) NOT NULL,
  `skills` varchar(200) NOT NULL,
  `avatar` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `accounts_user`
--

INSERT INTO `accounts_user` (`id`, `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`, `is_staff`, `is_active`, `date_joined`, `email`, `organization_type`, `organization`, `city`, `bio`, `favorite_category`, `skills`, `avatar`) VALUES
(1, 'pbkdf2_sha256$1000000$dqfohpvnnSIa5veuWOI2sI$grmOaTk6WuA7Af71YKlPwuuwREeiusi4ZRasr1lTKYY=', '2026-10-24 21:01:51.657097', 0, 'demo_amina', 'Amina', 'Ben Salah', 0, 1, '2026-10-01 20:32:34.708337', 'demo_amina@demo.ecoteams.local', 'student', 'Université (démo)', 'Tunis', 'Compte de démonstration EcoTeams — données fictives.', 'transport', '', ''),
(2, 'pbkdf2_sha256$1000000$rz39QiCn6ZjWuNur690U9h$U3mpJA2Ok+yAWkgsbOocMJtZSohYqz2cWAdaHqzQ8nc=', NULL, 0, 'demo_youssef', 'Youssef', 'Trabelsi', 0, 1, '2026-09-24 20:32:35.530768', 'demo_youssef@demo.ecoteams.local', 'student', 'Université (démo)', 'Ariana', 'Compte de démonstration EcoTeams — données fictives.', 'food', '', ''),
(3, 'pbkdf2_sha256$1000000$EVdLeXZrlm3pvsLkRMgdjj$FS+8zynnEaIla/0J6jz9irpZ9Bs+E1usTA+QZxEEXUo=', NULL, 0, 'demo_nour', 'Nour', 'Belhadj', 0, 1, '2026-09-18 20:32:36.349659', 'demo_nour@demo.ecoteams.local', 'student', 'Université (démo)', 'Tunis', 'Compte de démonstration EcoTeams — données fictives.', 'water', '', ''),
(4, 'pbkdf2_sha256$1000000$tFDsmPJGYlwWFwi2NXi6Lk$1JCnQHBJQeiJQvPVgS6gQ+dVQ5UWCpGEVvfeWgefTBU=', '2026-10-24 21:04:04.122003', 0, 'demo_lina', 'Lina', 'Haddad', 0, 1, '2026-09-04 20:32:37.276234', 'demo_lina@demo.ecoteams.local', 'employee', 'Entreprise (démo)', 'Sousse', 'Compte de démonstration EcoTeams — données fictives.', 'recycling', '', ''),
(5, 'pbkdf2_sha256$1000000$jg4IXzzrehWNtifkdRV1Cm$CrCvGiaeGjuJnj4y3Tw/3mejktIvyfQs+6KMeOkQ1lY=', NULL, 0, 'demo_karim', 'Karim', 'Jaziri', 0, 1, '2026-09-18 20:32:38.128077', 'demo_karim@demo.ecoteams.local', 'employee', 'Entreprise (démo)', 'Sousse', 'Compte de démonstration EcoTeams — données fictives.', 'consumption', '', ''),
(6, 'pbkdf2_sha256$1000000$NbQW4kajfT0fOHANRjHijQ$HkvqyB21ZTeMNOgy8qCBMOofZszR9yZfcAqZchKtFp4=', NULL, 0, 'demo_sarra', 'Sarra', 'Mansour', 0, 1, '2026-09-14 20:32:38.936401', 'demo_sarra@demo.ecoteams.local', 'association', 'Association (démo)', 'Sfax', 'Compte de démonstration EcoTeams — données fictives.', 'energy', '', ''),
(7, 'pbkdf2_sha256$1000000$GX8ErHfcHJmz0MthGomZUp$eB2rUjkjGF60NxtYmsEcrrkUb2i9m0sfaFMVmCiVCjY=', NULL, 0, 'demo_mehdi', 'Mehdi', 'Gharbi', 0, 1, '2026-09-07 20:32:39.805958', 'demo_mehdi@demo.ecoteams.local', 'student', 'Université (démo)', 'Sfax', 'Compte de démonstration EcoTeams — données fictives.', 'energy', '', ''),
(8, 'pbkdf2_sha256$1000000$e72wAibGel8FlAqt7tqOxv$DdK0NfaDj5Kz0qzaW1xwJnEHw6jJ0DHYhNU24xSjbpQ=', NULL, 0, 'demo_ines', 'Inès', 'Chaabane', 0, 1, '2026-09-04 20:32:40.636164', 'demo_ines@demo.ecoteams.local', 'employee', 'Entreprise (démo)', 'Bizerte', 'Compte de démonstration EcoTeams — données fictives.', 'water', '', ''),
(9, 'pbkdf2_sha256$1000000$6RLCqW9nOCzAvtXlKpKgNG$UncVBpISJbfBbAaZRfeglKjvYK9RvjTL/3ZYDqi4/do=', '2026-10-25 13:41:07.458487', 0, 'demo_omar', 'Omar', 'Ferchichi', 0, 1, '2026-10-01 20:32:41.497547', 'demo_omar@demo.ecoteams.local', 'association', 'Association (démo)', 'Nabeul', 'Compte de démonstration EcoTeams — données fictives.', 'water', '', ''),
(10, 'pbkdf2_sha256$1000000$0ZrmGTrTRe7cTZelxVQ3Qh$RBfBpoEWthIVU4pbup1QmLJbYXv0f0TEaoOtBkWcBWM=', NULL, 0, 'demo_moderateur', 'Salma', 'Ayari', 0, 1, '2026-09-06 20:32:42.346903', 'demo_moderateur@demo.ecoteams.local', 'other', 'Équipe EcoTeams (démo)', 'Tunis', 'Compte de démonstration EcoTeams — données fictives.', '', '', '');

-- --------------------------------------------------------

--
-- Structure de la table `accounts_user_groups`
--

CREATE TABLE `accounts_user_groups` (
  `id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `group_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `accounts_user_groups`
--

INSERT INTO `accounts_user_groups` (`id`, `user_id`, `group_id`) VALUES
(1, 1, 1),
(2, 2, 1),
(3, 3, 1),
(4, 4, 1),
(5, 5, 1),
(6, 6, 1),
(7, 7, 1),
(8, 8, 1),
(9, 9, 1),
(10, 10, 1),
(11, 10, 2);

-- --------------------------------------------------------

--
-- Structure de la table `accounts_user_user_permissions`
--

CREATE TABLE `accounts_user_user_permissions` (
  `id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `actions_actionsubmission`
--

CREATE TABLE `actions_actionsubmission` (
  `id` bigint(20) NOT NULL,
  `description` longtext NOT NULL,
  `performed_on` date NOT NULL,
  `quantity` decimal(8,2) DEFAULT NULL,
  `evidence` varchar(100) NOT NULL,
  `status` varchar(20) NOT NULL,
  `moderation_notes` longtext NOT NULL,
  `points_awarded` int(10) UNSIGNED NOT NULL CHECK (`points_awarded` >= 0),
  `co2_saved_kg` decimal(10,3) DEFAULT NULL,
  `reviewed_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `challenge_id` bigint(20) DEFAULT NULL,
  `reviewed_by_id` bigint(20) DEFAULT NULL,
  `team_id` bigint(20) DEFAULT NULL,
  `user_id` bigint(20) NOT NULL,
  `action_type_id` bigint(20) NOT NULL,
  `dedupe_key` varchar(120) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `actions_actionsubmission`
--

INSERT INTO `actions_actionsubmission` (`id`, `description`, `performed_on`, `quantity`, `evidence`, `status`, `moderation_notes`, `points_awarded`, `co2_saved_kg`, `reviewed_at`, `created_at`, `updated_at`, `challenge_id`, `reviewed_by_id`, `team_id`, `user_id`, `action_type_id`, `dedupe_key`) VALUES
(1, 'Trajet en métro léger plutôt qu’en voiture (démo).', '2026-10-12', 9.00, '', 'approved', 'Validé (démonstration).', 10, 1.080, '2026-10-13 10:46:00.000000', '2026-10-24 20:32:43.177647', '2026-10-24 20:32:43.198251', NULL, 10, 1, 1, 2, '1:2:2026-10-12'),
(2, 'Tri des emballages et du verre de la semaine (démo).', '2026-10-13', 3.00, '', 'approved', 'Validé (démonstration).', 10, NULL, '2026-10-14 10:05:00.000000', '2026-10-24 20:32:43.435925', '2026-10-24 20:32:43.474454', 2, 10, 2, 4, 4, '4:4:2026-10-13'),
(3, 'Trajet en métro léger plutôt qu’en voiture (démo).', '2026-10-14', 12.00, '', 'approved', 'Validé (démonstration).', 10, 1.440, '2026-10-15 10:34:00.000000', '2026-10-24 20:32:43.642170', '2026-10-24 20:32:43.658872', NULL, 10, 1, 1, 2, '1:2:2026-10-14'),
(4, 'Soupe préparée avec les légumes restants (démo).', '2026-10-15', NULL, '', 'approved', 'Validé (démonstration).', 10, NULL, '2026-10-16 10:18:00.000000', '2026-10-24 20:32:43.780585', '2026-10-24 20:32:43.802108', NULL, 10, 1, 2, 12, '2:12:2026-10-15'),
(5, 'Gourde et boîte réutilisable pour le déjeuner (démo).', '2026-10-15', NULL, '', 'approved', 'Validé (démonstration).', 5, NULL, '2026-10-16 10:09:00.000000', '2026-10-24 20:32:44.014157', '2026-10-24 20:32:44.037596', NULL, 10, 2, 5, 6, '5:6:2026-10-15'),
(6, 'Lessive à 30 °C à pleine charge (démo).', '2026-10-15', NULL, '', 'approved', 'Validé (démonstration).', 6, NULL, '2026-10-16 10:41:00.000000', '2026-10-24 20:32:44.147329', '2026-10-24 20:32:44.167534', NULL, 10, 3, 6, 8, '6:8:2026-10-15'),
(7, 'Trajet domicile – campus à vélo au lieu de la voiture (démo).', '2026-10-16', 6.00, '', 'approved', 'Validé (démonstration).', 15, 1.140, '2026-10-17 10:45:00.000000', '2026-10-24 20:32:44.266510', '2026-10-24 20:32:44.286192', 1, 10, 1, 1, 1, '1:1:2026-10-16'),
(8, 'Tri des emballages et du verre de la semaine (démo).', '2026-10-16', 3.00, '', 'approved', 'Validé (démonstration).', 10, NULL, '2026-10-17 10:19:00.000000', '2026-10-24 20:32:44.417354', '2026-10-24 20:32:44.439458', 2, 10, 2, 4, 4, '4:4:2026-10-16'),
(9, 'Récupération d’eau de pluie pour arroser le potager (démo).', '2026-10-16', 120.00, '', 'approved', 'Validé (démonstration).', 12, NULL, '2026-10-17 10:54:00.000000', '2026-10-24 20:32:44.554130', '2026-10-24 20:32:44.573132', NULL, 10, 4, 9, 10, '9:10:2026-10-16'),
(10, 'Trajet domicile – campus à vélo au lieu de la voiture (démo).', '2026-10-17', 9.00, '', 'approved', 'Validé (démonstration).', 15, 1.710, '2026-10-18 10:23:00.000000', '2026-10-24 20:32:44.668344', '2026-10-24 20:32:44.688737', 1, 10, 1, 1, 1, '1:1:2026-10-17'),
(11, 'Déjeuner végétarien au restaurant universitaire (démo).', '2026-10-17', 2.00, '', 'approved', 'Validé (démonstration).', 8, 3.000, '2026-10-18 10:29:00.000000', '2026-10-24 20:32:44.828067', '2026-10-24 20:32:44.840667', NULL, 10, 1, 3, 11, '3:11:2026-10-17'),
(12, 'Réparation d’une lampe de bureau au repair café (démo).', '2026-10-17', NULL, '', 'approved', 'Validé (démonstration).', 20, NULL, '2026-10-18 10:05:00.000000', '2026-10-24 20:32:44.964532', '2026-10-24 20:32:44.984189', NULL, 10, 2, 4, 5, '4:5:2026-10-17'),
(13, 'Extinction des multiprises et des appareils en veille (démo).', '2026-10-17', 3.00, '', 'approved', 'Validé (démonstration).', 8, 1.350, '2026-10-18 10:57:00.000000', '2026-10-24 20:32:45.121282', '2026-10-24 20:32:45.144568', 3, 10, 3, 6, 7, '6:7:2026-10-17'),
(14, 'Trajet domicile – campus à vélo au lieu de la voiture (démo).', '2026-10-18', 8.00, '', 'approved', 'Validé (démonstration).', 15, 1.520, '2026-10-19 10:35:00.000000', '2026-10-24 20:32:45.240666', '2026-10-24 20:32:45.262058', 1, 10, 1, 1, 1, '1:1:2026-10-18'),
(15, 'Trajet domicile – campus à vélo au lieu de la voiture (démo).', '2026-10-18', 4.00, '', 'approved', 'Validé (démonstration).', 15, 0.760, '2026-10-19 10:55:00.000000', '2026-10-24 20:32:45.450411', '2026-10-24 20:32:45.470420', 1, 10, 1, 2, 1, '2:1:2026-10-18'),
(16, 'Tri des emballages et du verre de la semaine (démo).', '2026-10-18', 3.00, '', 'approved', 'Validé (démonstration).', 10, NULL, '2026-10-19 10:27:00.000000', '2026-10-24 20:32:45.605592', '2026-10-24 20:32:45.627064', 2, 10, 2, 4, 4, '4:4:2026-10-18'),
(17, 'Extinction des multiprises et des appareils en veille (démo).', '2026-10-18', 3.00, '', 'approved', 'Validé (démonstration).', 8, 1.350, '2026-10-19 10:51:00.000000', '2026-10-24 20:32:45.766114', '2026-10-24 20:32:45.786781', NULL, 10, 2, 5, 7, '5:7:2026-10-18'),
(18, 'Covoiturage avec deux collègues pour aller au travail (démo).', '2026-10-18', 18.00, '', 'approved', 'Validé (démonstration).', 8, 1.620, '2026-10-19 10:55:00.000000', '2026-10-24 20:32:45.852362', '2026-10-24 20:32:45.868785', NULL, 10, 3, 7, 3, '7:3:2026-10-18'),
(19, 'Douche chronométrée de 4 minutes (démo).', '2026-10-18', NULL, '', 'approved', 'Validé (démonstration).', 6, NULL, '2026-10-19 10:56:00.000000', '2026-10-24 20:32:45.966052', '2026-10-24 20:32:45.985468', 4, 10, 4, 9, 9, '9:9:2026-10-18'),
(20, 'Trajet domicile – campus à vélo au lieu de la voiture (démo).', '2026-10-19', 7.00, '', 'approved', 'Validé (démonstration).', 15, 1.330, '2026-10-20 10:25:00.000000', '2026-10-24 20:32:46.089866', '2026-10-24 20:32:46.110949', 1, 10, 1, 1, 1, '1:1:2026-10-19'),
(21, 'Déjeuner végétarien au restaurant universitaire (démo).', '2026-10-19', 1.00, '', 'approved', 'Validé (démonstration).', 8, 1.500, '2026-10-20 10:33:00.000000', '2026-10-24 20:32:46.289696', '2026-10-24 20:32:46.306520', NULL, 10, 1, 2, 11, '2:11:2026-10-19'),
(22, 'Trajet en métro léger plutôt qu’en voiture (démo).', '2026-10-19', 11.00, '', 'approved', 'Validé (démonstration).', 10, 1.320, '2026-10-20 10:54:00.000000', '2026-10-24 20:32:46.453276', '2026-10-24 20:32:46.472461', NULL, 10, 1, 3, 2, '3:2:2026-10-19'),
(23, 'Tri des emballages et du verre de la semaine (démo).', '2026-10-19', 4.00, '', 'approved', 'Validé (démonstration).', 10, NULL, '2026-10-20 10:36:00.000000', '2026-10-24 20:32:46.579700', '2026-10-24 20:32:46.597798', 2, 10, 2, 5, 4, '5:4:2026-10-19'),
(24, 'Extinction des multiprises et des appareils en veille (démo).', '2026-10-19', 4.00, '', 'approved', 'Validé (démonstration).', 8, 1.800, '2026-10-20 10:30:00.000000', '2026-10-24 20:32:46.673749', '2026-10-24 20:32:46.692060', 3, 10, 3, 6, 7, '6:7:2026-10-19'),
(25, 'Extinction des multiprises et des appareils en veille (démo).', '2026-10-19', 1.00, '', 'approved', 'Validé (démonstration).', 8, 0.450, '2026-10-20 10:33:00.000000', '2026-10-24 20:32:46.774982', '2026-10-24 20:32:46.796705', NULL, 10, 3, 8, 7, '8:7:2026-10-19'),
(26, 'Douche chronométrée de 4 minutes (démo).', '2026-10-19', NULL, '', 'approved', 'Validé (démonstration).', 6, NULL, '2026-10-20 10:01:00.000000', '2026-10-24 20:32:46.887311', '2026-10-24 20:32:46.907523', 4, 10, 4, 9, 9, '9:9:2026-10-19'),
(27, 'Trajet domicile – campus à vélo au lieu de la voiture (démo).', '2026-10-20', 6.00, '', 'approved', 'Validé (démonstration).', 15, 1.140, '2026-10-21 10:14:00.000000', '2026-10-24 20:32:47.001860', '2026-10-24 20:32:47.021481', 1, 10, 1, 1, 1, '1:1:2026-10-20'),
(28, 'Trajet domicile – campus à vélo au lieu de la voiture (démo).', '2026-10-20', 7.00, '', 'approved', 'Validé (démonstration).', 15, 1.330, '2026-10-21 10:08:00.000000', '2026-10-24 20:32:47.176853', '2026-10-24 20:32:47.192429', 1, 10, 1, 2, 1, '2:1:2026-10-20'),
(29, 'Douche chronométrée de 4 minutes (démo).', '2026-10-20', NULL, '', 'approved', 'Validé (démonstration).', 6, NULL, '2026-10-21 10:03:00.000000', '2026-10-24 20:32:47.333286', '2026-10-24 20:32:47.351524', 4, 10, 1, 3, 9, '3:9:2026-10-20'),
(30, 'Tri des emballages et du verre de la semaine (démo).', '2026-10-20', 3.00, '', 'approved', 'Validé (démonstration).', 10, NULL, '2026-10-21 10:33:00.000000', '2026-10-24 20:32:47.494507', '2026-10-24 20:32:47.526583', 2, 10, 2, 4, 4, '4:4:2026-10-20'),
(31, 'Lessive à 30 °C à pleine charge (démo).', '2026-10-20', NULL, '', 'approved', 'Validé (démonstration).', 6, NULL, '2026-10-21 10:42:00.000000', '2026-10-24 20:32:47.625316', '2026-10-24 20:32:47.646905', NULL, 10, 3, 6, 8, '6:8:2026-10-20'),
(32, 'Extinction des multiprises et des appareils en veille (démo).', '2026-10-20', 2.00, '', 'approved', 'Validé (démonstration).', 8, 0.900, '2026-10-21 10:45:00.000000', '2026-10-24 20:32:47.736697', '2026-10-24 20:32:47.757858', 3, 10, 3, 7, 7, '7:7:2026-10-20'),
(33, 'Douche chronométrée de 4 minutes (démo).', '2026-10-20', NULL, '', 'approved', 'Validé (démonstration).', 6, NULL, '2026-10-21 10:27:00.000000', '2026-10-24 20:32:47.843084', '2026-10-24 20:32:47.868686', 4, 10, 4, 9, 9, '9:9:2026-10-20'),
(34, 'Trajet domicile – campus à vélo au lieu de la voiture (démo).', '2026-10-21', 9.00, '', 'approved', 'Validé (démonstration).', 15, 1.710, '2026-10-22 10:09:00.000000', '2026-10-24 20:32:47.953001', '2026-10-24 20:32:47.967244', 1, 10, 1, 1, 1, '1:1:2026-10-21'),
(35, 'Trajet domicile – campus à vélo au lieu de la voiture (démo).', '2026-10-21', 5.00, '', 'approved', 'Validé (démonstration).', 15, 0.950, '2026-10-22 10:56:00.000000', '2026-10-24 20:32:48.053973', '2026-10-24 20:32:48.061055', 1, 10, 1, 2, 1, '2:1:2026-10-21'),
(36, 'Douche chronométrée de 4 minutes (démo).', '2026-10-21', NULL, '', 'approved', 'Validé (démonstration).', 6, NULL, '2026-10-22 10:54:00.000000', '2026-10-24 20:32:48.166797', '2026-10-24 20:32:48.180674', 4, 10, 1, 3, 9, '3:9:2026-10-21'),
(37, 'Gourde et boîte réutilisable pour le déjeuner (démo).', '2026-10-21', NULL, '', 'approved', 'Validé (démonstration).', 5, NULL, '2026-10-22 10:07:00.000000', '2026-10-24 20:32:48.269726', '2026-10-24 20:32:48.287737', NULL, 10, 2, 4, 6, '4:6:2026-10-21'),
(38, 'Extinction des multiprises et des appareils en veille (démo).', '2026-10-21', 2.00, '', 'approved', 'Validé (démonstration).', 8, 0.900, '2026-10-22 10:44:00.000000', '2026-10-24 20:32:48.374338', '2026-10-24 20:32:48.391562', 3, 10, 3, 6, 7, '6:7:2026-10-21'),
(39, 'Douche chronométrée de 4 minutes (démo).', '2026-10-21', NULL, '', 'approved', 'Validé (démonstration).', 6, NULL, '2026-10-22 10:43:00.000000', '2026-10-24 20:32:48.492483', '2026-10-24 20:32:48.513080', 4, 10, 3, 8, 9, '8:9:2026-10-21'),
(40, 'Douche chronométrée de 4 minutes (démo).', '2026-10-21', NULL, '', 'approved', 'Validé (démonstration).', 6, NULL, '2026-10-22 10:45:00.000000', '2026-10-24 20:32:48.638384', '2026-10-24 20:32:48.657861', 4, 10, 4, 9, 9, '9:9:2026-10-21'),
(41, 'Trajet domicile – campus à vélo au lieu de la voiture (démo).', '2026-10-22', 8.00, '', 'approved', 'Validé (démonstration).', 15, 1.520, '2026-10-23 10:34:00.000000', '2026-10-24 20:32:48.787748', '2026-10-24 20:32:48.862940', 1, 10, 1, 1, 1, '1:1:2026-10-22'),
(42, 'Trajet en métro léger plutôt qu’en voiture (démo).', '2026-10-22', 15.00, '', 'approved', 'Validé (démonstration).', 10, 1.800, '2026-10-23 10:35:00.000000', '2026-10-24 20:32:49.091938', '2026-10-24 20:32:49.113458', NULL, 10, 1, 3, 2, '3:2:2026-10-22'),
(43, 'Tri des emballages et du verre de la semaine (démo).', '2026-10-22', 3.00, '', 'approved', 'Validé (démonstration).', 10, NULL, '2026-10-23 10:42:00.000000', '2026-10-24 20:32:49.232274', '2026-10-24 20:32:49.248568', 2, 10, 2, 4, 4, '4:4:2026-10-22'),
(44, 'Tri des emballages et du verre de la semaine (démo).', '2026-10-22', 2.00, '', 'approved', 'Validé (démonstration).', 10, NULL, '2026-10-23 10:35:00.000000', '2026-10-24 20:32:49.329715', '2026-10-24 20:32:49.346192', 2, 10, 2, 5, 4, '5:4:2026-10-22'),
(45, 'Extinction des multiprises et des appareils en veille (démo).', '2026-10-22', 4.00, '', 'approved', 'Validé (démonstration).', 8, 1.800, '2026-10-23 10:41:00.000000', '2026-10-24 20:32:49.428964', '2026-10-24 20:32:49.451677', 3, 10, 3, 6, 7, '6:7:2026-10-22'),
(46, 'Extinction des multiprises et des appareils en veille (démo).', '2026-10-22', 1.50, '', 'approved', 'Validé (démonstration).', 8, 0.675, '2026-10-23 10:44:00.000000', '2026-10-24 20:32:49.581661', '2026-10-24 20:32:49.600043', 3, 10, 3, 7, 7, '7:7:2026-10-22'),
(47, 'Douche chronométrée de 4 minutes (démo).', '2026-10-22', NULL, '', 'approved', 'Validé (démonstration).', 6, NULL, '2026-10-23 10:51:00.000000', '2026-10-24 20:32:49.685622', '2026-10-24 20:32:49.702279', 4, 10, 3, 8, 9, '8:9:2026-10-22'),
(48, 'Douche chronométrée de 4 minutes (démo).', '2026-10-22', NULL, '', 'approved', 'Validé (démonstration).', 6, NULL, '2026-10-23 10:25:00.000000', '2026-10-24 20:32:49.821942', '2026-10-24 20:32:49.842068', 4, 10, 4, 9, 9, '9:9:2026-10-22'),
(49, 'Trajet domicile – campus à vélo au lieu de la voiture (démo).', '2026-10-23', 7.00, '', 'approved', 'Validé (démonstration).', 15, 1.330, '2026-10-24 10:12:00.000000', '2026-10-24 20:32:49.963210', '2026-10-24 20:32:49.982410', 1, 10, 1, 1, 1, '1:1:2026-10-23'),
(50, 'Tri des emballages et du verre de la semaine (démo).', '2026-10-23', 3.00, '', 'approved', 'Validé (démonstration).', 10, NULL, '2026-10-24 10:53:00.000000', '2026-10-24 20:32:50.116680', '2026-10-24 20:32:50.137994', 2, 10, 2, 4, 4, '4:4:2026-10-23'),
(51, 'Extinction des multiprises et des appareils en veille (démo).', '2026-10-23', 3.00, '', 'approved', 'Validé (démonstration).', 8, 1.350, '2026-10-24 10:00:00.000000', '2026-10-24 20:32:50.268097', '2026-10-24 20:32:50.289570', 3, 10, 3, 6, 7, '6:7:2026-10-23'),
(52, 'Douche chronométrée de 4 minutes (démo).', '2026-10-23', NULL, '', 'approved', 'Validé (démonstration).', 6, NULL, '2026-10-24 10:09:00.000000', '2026-10-24 20:32:50.391234', '2026-10-24 20:32:50.411482', 4, 10, 3, 8, 9, '8:9:2026-10-23'),
(53, 'Douche chronométrée de 4 minutes (démo).', '2026-10-23', NULL, '', 'approved', 'Validé (démonstration).', 6, NULL, '2026-10-24 10:56:00.000000', '2026-10-24 20:32:50.503612', '2026-10-24 20:32:50.523870', 4, 10, 4, 9, 9, '9:9:2026-10-23'),
(54, 'Trajet en bus jusqu’au campus ce matin (démo, en attente).', '2026-10-24', 8.00, '', 'pending', '', 0, NULL, NULL, '2026-10-24 20:32:50.612353', '2026-10-24 20:32:50.612393', NULL, NULL, NULL, 1, 2, '1:2:2026-10-24'),
(55, 'Tri des emballages de la cafétéria (démo, en attente).', '2026-10-24', 3.00, '', 'pending', '', 0, NULL, NULL, '2026-10-24 20:32:50.627854', '2026-10-24 20:32:50.627904', NULL, NULL, NULL, 5, 4, '5:4:2026-10-24'),
(56, 'Extinction des écrans de la salle informatique (démo, en attente).', '2026-10-23', 2.00, '', 'pending', '', 0, NULL, NULL, '2026-10-24 20:32:50.644797', '2026-10-24 20:32:50.644863', NULL, NULL, NULL, 7, 7, '7:7:2026-10-23'),
(57, 'Préparation d’un repas avec les restes de la veille (démo, en attente).', '2026-10-23', NULL, '', 'pending', '', 0, NULL, NULL, '2026-10-24 20:32:50.660658', '2026-10-24 20:32:50.660698', NULL, NULL, NULL, 8, 12, '8:12:2026-10-23'),
(58, 'Réparation déclarée sans photo (démo).', '2026-10-22', NULL, '', 'rejected', 'La photo justificative est obligatoire pour cette action.', 0, NULL, '2026-10-24 20:32:50.692541', '2026-10-24 20:32:50.676229', '2026-10-24 20:32:50.692658', NULL, 10, NULL, 2, 5, NULL);

-- --------------------------------------------------------

--
-- Structure de la table `actions_ecoactiontype`
--

CREATE TABLE `actions_ecoactiontype` (
  `id` bigint(20) NOT NULL,
  `name` varchar(120) NOT NULL,
  `slug` varchar(130) NOT NULL,
  `description` longtext NOT NULL,
  `category` varchar(20) NOT NULL,
  `points` int(10) UNSIGNED NOT NULL CHECK (`points` >= 0),
  `unit` varchar(30) NOT NULL,
  `co2_factor_kg` decimal(8,3) DEFAULT NULL,
  `factor_source` varchar(255) NOT NULL,
  `instructions` longtext NOT NULL,
  `requires_evidence` tinyint(1) NOT NULL,
  `requires_quantity` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL
) ;

--
-- Déchargement des données de la table `actions_ecoactiontype`
--

INSERT INTO `actions_ecoactiontype` (`id`, `name`, `slug`, `description`, `category`, `points`, `unit`, `co2_factor_kg`, `factor_source`, `instructions`, `requires_evidence`, `requires_quantity`, `is_active`, `created_at`, `updated_at`) VALUES
(1, 'Trajet à vélo ou à pied', 'trajet-a-velo-ou-a-pied', 'Remplacer un trajet en voiture par le vélo, la trottinette ou la marche.', 'transport', 15, 'km', 0.190, 'Valeur indicative de démonstration — à remplacer par une valeur sourcée (ex. Base Empreinte® de l’ADEME ou facteur national) avant tout usage réel.', 'Indiquez la distance parcourue et le trajet effectué.', 0, 1, 1, '2026-10-24 20:32:33.457077', '2026-10-24 20:32:33.457180'),
(2, 'Transports en commun plutôt que la voiture', 'transports-en-commun-plutot-que-la-voiture', 'Prendre le bus, le métro, le train ou le tramway au lieu de la voiture individuelle.', 'transport', 10, 'km', 0.120, 'Valeur indicative de démonstration — à remplacer par une valeur sourcée (ex. Base Empreinte® de l’ADEME ou facteur national) avant tout usage réel.', 'Précisez la ligne ou le trajet.', 0, 1, 1, '2026-10-24 20:32:33.465536', '2026-10-24 20:32:33.465607'),
(3, 'Covoiturage', 'covoiturage', 'Partager un trajet en voiture avec au moins une autre personne.', 'transport', 8, 'km', 0.090, 'Valeur indicative de démonstration — à remplacer par une valeur sourcée (ex. Base Empreinte® de l’ADEME ou facteur national) avant tout usage réel.', '', 0, 1, 1, '2026-10-24 20:32:33.483498', '2026-10-24 20:32:33.483576'),
(4, 'Tri sélectif des déchets', 'tri-selectif-des-dechets', 'Trier correctement les emballages, le verre et le papier du foyer ou du bureau.', 'recycling', 10, 'kg', NULL, '', 'Décrivez les flux triés. Une photo des bacs est appréciée.', 0, 0, 1, '2026-10-24 20:32:33.492214', '2026-10-24 20:32:33.492318'),
(5, 'Réparer au lieu de jeter', 'reparer-au-lieu-de-jeter', 'Faire réparer ou réparer soi-même un objet plutôt que d’en racheter un neuf.', 'consumption', 20, '', NULL, '', 'Photo de l’objet réparé obligatoire.', 1, 0, 1, '2026-10-24 20:32:33.500589', '2026-10-24 20:32:33.500707'),
(6, 'Gourde et contenants réutilisables', 'gourde-et-contenants-reutilisables', 'Éviter les bouteilles et emballages jetables grâce à des contenants réutilisables.', 'consumption', 5, '', NULL, '', '', 0, 0, 1, '2026-10-24 20:32:33.508507', '2026-10-24 20:32:33.508542'),
(7, 'Éteindre les appareils en veille', 'eteindre-les-appareils-en-veille', 'Couper multiprises et appareils en veille (maison, salle de cours, bureau).', 'energy', 8, 'kWh', 0.450, 'Valeur indicative de démonstration — à remplacer par une valeur sourcée (ex. Base Empreinte® de l’ADEME ou facteur national) avant tout usage réel.', 'Estimez l’énergie économisée si possible.', 0, 0, 1, '2026-10-24 20:32:33.514247', '2026-10-24 20:32:33.514296'),
(8, 'Lessive à basse température', 'lessive-a-basse-temperature', 'Laver son linge à 30 °C ou moins, à pleine charge.', 'energy', 6, '', NULL, '', '', 0, 0, 1, '2026-10-24 20:32:33.519592', '2026-10-24 20:32:33.519641'),
(9, 'Douche de moins de 5 minutes', 'douche-de-moins-de-5-minutes', 'Limiter la durée de la douche pour économiser l’eau et l’énergie de chauffage.', 'water', 6, '', NULL, '', '', 0, 0, 1, '2026-10-24 20:32:33.524868', '2026-10-24 20:32:33.524918'),
(10, 'Récupération d’eau de pluie', 'recuperation-deau-de-pluie', 'Récupérer l’eau de pluie pour l’arrosage ou le nettoyage.', 'water', 12, 'L', NULL, '', 'Photo du dispositif obligatoire.', 1, 1, 1, '2026-10-24 20:32:33.532984', '2026-10-24 20:32:33.533035'),
(11, 'Repas végétarien', 'repas-vegetarien', 'Choisir un repas végétarien à la place d’un repas avec viande.', 'food', 8, 'repas', 1.500, 'Valeur indicative de démonstration — à remplacer par une valeur sourcée (ex. Base Empreinte® de l’ADEME ou facteur national) avant tout usage réel.', '', 0, 1, 1, '2026-10-24 20:32:33.539445', '2026-10-24 20:32:33.539519'),
(12, 'Lutte contre le gaspillage alimentaire', 'lutte-contre-le-gaspillage-alimentaire', 'Cuisiner les restes, donner les invendus, planifier ses courses.', 'food', 10, '', NULL, '', '', 0, 0, 1, '2026-10-24 20:32:33.548338', '2026-10-24 20:32:33.548421');

-- --------------------------------------------------------

--
-- Structure de la table `actions_moderationlog`
--

CREATE TABLE `actions_moderationlog` (
  `id` bigint(20) NOT NULL,
  `decision` varchar(20) NOT NULL,
  `previous_status` varchar(20) NOT NULL,
  `new_status` varchar(20) NOT NULL,
  `notes` longtext NOT NULL,
  `points_delta` int(11) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `moderator_id` bigint(20) DEFAULT NULL,
  `submission_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `actions_moderationlog`
--

INSERT INTO `actions_moderationlog` (`id`, `decision`, `previous_status`, `new_status`, `notes`, `points_delta`, `created_at`, `moderator_id`, `submission_id`) VALUES
(1, 'approved', 'pending', 'approved', 'Validé (démonstration).', 10, '2026-10-13 10:46:00.000000', 10, 1),
(2, 'approved', 'pending', 'approved', 'Validé (démonstration).', 10, '2026-10-14 10:05:00.000000', 10, 2),
(3, 'approved', 'pending', 'approved', 'Validé (démonstration).', 10, '2026-10-15 10:34:00.000000', 10, 3),
(4, 'approved', 'pending', 'approved', 'Validé (démonstration).', 10, '2026-10-16 10:18:00.000000', 10, 4),
(5, 'approved', 'pending', 'approved', 'Validé (démonstration).', 5, '2026-10-16 10:09:00.000000', 10, 5),
(6, 'approved', 'pending', 'approved', 'Validé (démonstration).', 6, '2026-10-16 10:41:00.000000', 10, 6),
(7, 'approved', 'pending', 'approved', 'Validé (démonstration).', 15, '2026-10-17 10:45:00.000000', 10, 7),
(8, 'approved', 'pending', 'approved', 'Validé (démonstration).', 10, '2026-10-17 10:19:00.000000', 10, 8),
(9, 'approved', 'pending', 'approved', 'Validé (démonstration).', 12, '2026-10-17 10:54:00.000000', 10, 9),
(10, 'approved', 'pending', 'approved', 'Validé (démonstration).', 15, '2026-10-18 10:23:00.000000', 10, 10),
(11, 'approved', 'pending', 'approved', 'Validé (démonstration).', 8, '2026-10-18 10:29:00.000000', 10, 11),
(12, 'approved', 'pending', 'approved', 'Validé (démonstration).', 20, '2026-10-18 10:05:00.000000', 10, 12),
(13, 'approved', 'pending', 'approved', 'Validé (démonstration).', 8, '2026-10-18 10:57:00.000000', 10, 13),
(14, 'approved', 'pending', 'approved', 'Validé (démonstration).', 15, '2026-10-19 10:35:00.000000', 10, 14),
(15, 'approved', 'pending', 'approved', 'Validé (démonstration).', 15, '2026-10-19 10:55:00.000000', 10, 15),
(16, 'approved', 'pending', 'approved', 'Validé (démonstration).', 10, '2026-10-19 10:27:00.000000', 10, 16),
(17, 'approved', 'pending', 'approved', 'Validé (démonstration).', 8, '2026-10-19 10:51:00.000000', 10, 17),
(18, 'approved', 'pending', 'approved', 'Validé (démonstration).', 8, '2026-10-19 10:55:00.000000', 10, 18),
(19, 'approved', 'pending', 'approved', 'Validé (démonstration).', 6, '2026-10-19 10:56:00.000000', 10, 19),
(20, 'approved', 'pending', 'approved', 'Validé (démonstration).', 15, '2026-10-20 10:25:00.000000', 10, 20),
(21, 'approved', 'pending', 'approved', 'Validé (démonstration).', 8, '2026-10-20 10:33:00.000000', 10, 21),
(22, 'approved', 'pending', 'approved', 'Validé (démonstration).', 10, '2026-10-20 10:54:00.000000', 10, 22),
(23, 'approved', 'pending', 'approved', 'Validé (démonstration).', 10, '2026-10-20 10:36:00.000000', 10, 23),
(24, 'approved', 'pending', 'approved', 'Validé (démonstration).', 8, '2026-10-20 10:30:00.000000', 10, 24),
(25, 'approved', 'pending', 'approved', 'Validé (démonstration).', 8, '2026-10-20 10:33:00.000000', 10, 25),
(26, 'approved', 'pending', 'approved', 'Validé (démonstration).', 6, '2026-10-20 10:01:00.000000', 10, 26),
(27, 'approved', 'pending', 'approved', 'Validé (démonstration).', 15, '2026-10-21 10:14:00.000000', 10, 27),
(28, 'approved', 'pending', 'approved', 'Validé (démonstration).', 15, '2026-10-21 10:08:00.000000', 10, 28),
(29, 'approved', 'pending', 'approved', 'Validé (démonstration).', 6, '2026-10-21 10:03:00.000000', 10, 29),
(30, 'approved', 'pending', 'approved', 'Validé (démonstration).', 10, '2026-10-21 10:33:00.000000', 10, 30),
(31, 'approved', 'pending', 'approved', 'Validé (démonstration).', 6, '2026-10-21 10:42:00.000000', 10, 31),
(32, 'approved', 'pending', 'approved', 'Validé (démonstration).', 8, '2026-10-21 10:45:00.000000', 10, 32),
(33, 'approved', 'pending', 'approved', 'Validé (démonstration).', 6, '2026-10-21 10:27:00.000000', 10, 33),
(34, 'approved', 'pending', 'approved', 'Validé (démonstration).', 15, '2026-10-22 10:09:00.000000', 10, 34),
(35, 'approved', 'pending', 'approved', 'Validé (démonstration).', 15, '2026-10-22 10:56:00.000000', 10, 35),
(36, 'approved', 'pending', 'approved', 'Validé (démonstration).', 6, '2026-10-22 10:54:00.000000', 10, 36),
(37, 'approved', 'pending', 'approved', 'Validé (démonstration).', 5, '2026-10-22 10:07:00.000000', 10, 37),
(38, 'approved', 'pending', 'approved', 'Validé (démonstration).', 8, '2026-10-22 10:44:00.000000', 10, 38),
(39, 'approved', 'pending', 'approved', 'Validé (démonstration).', 6, '2026-10-22 10:43:00.000000', 10, 39),
(40, 'approved', 'pending', 'approved', 'Validé (démonstration).', 6, '2026-10-22 10:45:00.000000', 10, 40),
(41, 'approved', 'pending', 'approved', 'Validé (démonstration).', 15, '2026-10-23 10:34:00.000000', 10, 41),
(42, 'approved', 'pending', 'approved', 'Validé (démonstration).', 10, '2026-10-23 10:35:00.000000', 10, 42),
(43, 'approved', 'pending', 'approved', 'Validé (démonstration).', 10, '2026-10-23 10:42:00.000000', 10, 43),
(44, 'approved', 'pending', 'approved', 'Validé (démonstration).', 10, '2026-10-23 10:35:00.000000', 10, 44),
(45, 'approved', 'pending', 'approved', 'Validé (démonstration).', 8, '2026-10-23 10:41:00.000000', 10, 45),
(46, 'approved', 'pending', 'approved', 'Validé (démonstration).', 8, '2026-10-23 10:44:00.000000', 10, 46),
(47, 'approved', 'pending', 'approved', 'Validé (démonstration).', 6, '2026-10-23 10:51:00.000000', 10, 47),
(48, 'approved', 'pending', 'approved', 'Validé (démonstration).', 6, '2026-10-23 10:25:00.000000', 10, 48),
(49, 'approved', 'pending', 'approved', 'Validé (démonstration).', 15, '2026-10-24 10:12:00.000000', 10, 49),
(50, 'approved', 'pending', 'approved', 'Validé (démonstration).', 10, '2026-10-24 10:53:00.000000', 10, 50),
(51, 'approved', 'pending', 'approved', 'Validé (démonstration).', 8, '2026-10-24 10:00:00.000000', 10, 51),
(52, 'approved', 'pending', 'approved', 'Validé (démonstration).', 6, '2026-10-24 10:09:00.000000', 10, 52),
(53, 'approved', 'pending', 'approved', 'Validé (démonstration).', 6, '2026-10-24 10:56:00.000000', 10, 53),
(54, 'rejected', 'pending', 'rejected', 'La photo justificative est obligatoire pour cette action.', 0, '2026-10-24 20:32:50.693667', 10, 58);

-- --------------------------------------------------------

--
-- Structure de la table `analytics_activitylog`
--

CREATE TABLE `analytics_activitylog` (
  `id` bigint(20) NOT NULL,
  `verb` varchar(30) NOT NULL,
  `description` varchar(255) NOT NULL,
  `link` varchar(255) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `actor_id` bigint(20) NOT NULL,
  `team_id` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `analytics_activitylog`
--

INSERT INTO `analytics_activitylog` (`id`, `verb`, `description`, `link`, `created_at`, `actor_id`, `team_id`) VALUES
(1, 'team_created', 'Amina Ben Salah a créé l’équipe « Les Pédaleurs Verts ».', '/teams/les-pedaleurs-verts/', '2026-09-24 10:57:00.000000', 1, 1),
(2, 'team_joined', 'Youssef Trabelsi a rejoint l’équipe « Les Pédaleurs Verts ».', '/teams/les-pedaleurs-verts/', '2026-09-26 12:35:00.000000', 2, 1),
(3, 'team_joined', 'Nour Belhadj a rejoint l’équipe « Les Pédaleurs Verts ».', '/teams/les-pedaleurs-verts/', '2026-09-27 12:50:00.000000', 3, 1),
(4, 'team_created', 'Lina Haddad a créé l’équipe « Zéro Déchet Squad ».', '/teams/zero-dechet-squad/', '2026-09-24 10:35:00.000000', 4, 2),
(5, 'team_joined', 'Karim Jaziri a rejoint l’équipe « Zéro Déchet Squad ».', '/teams/zero-dechet-squad/', '2026-09-26 12:49:00.000000', 5, 2),
(6, 'team_created', 'Sarra Mansour a créé l’équipe « Watt Watchers ».', '/teams/watt-watchers/', '2026-09-24 10:31:00.000000', 6, 3),
(7, 'team_joined', 'Mehdi Gharbi a rejoint l’équipe « Watt Watchers ».', '/teams/watt-watchers/', '2026-09-26 12:37:00.000000', 7, 3),
(8, 'team_joined', 'Inès Chaabane a rejoint l’équipe « Watt Watchers ».', '/teams/watt-watchers/', '2026-09-27 12:15:00.000000', 8, 3),
(9, 'team_created', 'Omar Ferchichi a créé l’équipe « Gouttes d’Avenir ».', '/teams/gouttes-davenir/', '2026-09-24 10:39:00.000000', 9, 4),
(10, 'team_created', 'Salma Ayari a créé l’équipe « Consom’Acteurs ».', '/teams/consomacteurs/', '2026-09-24 10:18:00.000000', 10, 5),
(11, 'challenge_published', 'Le défi « Mois du vélo » est maintenant actif.', '/challenges/mois-du-velo/', '2026-10-24 20:32:42.642481', 10, NULL),
(12, 'challenge_published', 'Le défi « Tri sélectif au quotidien » est maintenant actif.', '/challenges/tri-selectif-au-quotidien/', '2026-10-24 20:32:42.688005', 10, NULL),
(13, 'challenge_published', 'Le défi « Chasse au gaspillage énergétique » est maintenant actif.', '/challenges/chasse-au-gaspillage-energetique/', '2026-10-24 20:32:42.725115', 10, NULL),
(14, 'challenge_published', 'Le défi « Douches express » est maintenant actif.', '/challenges/douches-express/', '2026-10-24 20:32:42.764548', 10, NULL),
(15, 'challenge_published', 'Le défi « Semaine du covoiturage » est maintenant actif.', '/challenges/semaine-du-covoiturage/', '2026-10-24 20:32:42.823169', 10, NULL),
(16, 'challenge_joined', 'Amina Ben Salah relève le défi « Mois du vélo ».', '/challenges/mois-du-velo/', '2026-10-24 20:32:42.920404', 1, 1),
(17, 'challenge_joined', 'Youssef Trabelsi relève le défi « Mois du vélo ».', '/challenges/mois-du-velo/', '2026-10-24 20:32:42.935965', 2, 1),
(18, 'challenge_joined', 'Nour Belhadj relève le défi « Mois du vélo ».', '/challenges/mois-du-velo/', '2026-10-24 20:32:42.959949', 3, 1),
(19, 'challenge_joined', 'Mehdi Gharbi relève le défi « Mois du vélo ».', '/challenges/mois-du-velo/', '2026-10-24 20:32:42.974301', 7, 3),
(20, 'challenge_joined', 'Lina Haddad relève le défi « Tri sélectif au quotidien ».', '/challenges/tri-selectif-au-quotidien/', '2026-10-24 20:32:42.987649', 4, 2),
(21, 'challenge_joined', 'Karim Jaziri relève le défi « Tri sélectif au quotidien ».', '/challenges/tri-selectif-au-quotidien/', '2026-10-24 20:32:43.000501', 5, 2),
(22, 'challenge_joined', 'Youssef Trabelsi relève le défi « Tri sélectif au quotidien ».', '/challenges/tri-selectif-au-quotidien/', '2026-10-24 20:32:43.013215', 2, 1),
(23, 'challenge_joined', 'Sarra Mansour relève le défi « Chasse au gaspillage énergétique ».', '/challenges/chasse-au-gaspillage-energetique/', '2026-10-24 20:32:43.026732', 6, 3),
(24, 'challenge_joined', 'Mehdi Gharbi relève le défi « Chasse au gaspillage énergétique ».', '/challenges/chasse-au-gaspillage-energetique/', '2026-10-24 20:32:43.038972', 7, 3),
(25, 'challenge_joined', 'Inès Chaabane relève le défi « Chasse au gaspillage énergétique ».', '/challenges/chasse-au-gaspillage-energetique/', '2026-10-24 20:32:43.051748', 8, 3),
(26, 'challenge_joined', 'Omar Ferchichi relève le défi « Douches express ».', '/challenges/douches-express/', '2026-10-24 20:32:43.065206', 9, 4),
(27, 'challenge_joined', 'Inès Chaabane relève le défi « Douches express ».', '/challenges/douches-express/', '2026-10-24 20:32:43.083095', 8, 3),
(28, 'challenge_joined', 'Nour Belhadj relève le défi « Douches express ».', '/challenges/douches-express/', '2026-10-24 20:32:43.096953', 3, 1),
(29, 'challenge_joined', 'Youssef Trabelsi relève le défi « Semaine du covoiturage ».', '/challenges/semaine-du-covoiturage/', '2026-10-24 20:32:43.110988', 2, 1),
(30, 'challenge_joined', 'Karim Jaziri relève le défi « Semaine du covoiturage ».', '/challenges/semaine-du-covoiturage/', '2026-10-24 20:32:43.123913', 5, 2),
(31, 'action_submitted', 'Amina Ben Salah a déclaré l’action « Transports en commun plutôt que la voiture ».', '/actions/1/', '2026-10-12 17:04:00.000000', 1, 1),
(32, 'action_approved', 'Action validée : « Transports en commun plutôt que la voiture » (+10 pts).', '/actions/1/', '2026-10-13 10:46:00.000000', 1, 1),
(33, 'badge_unlocked', 'Amina Ben Salah a débloqué le badge « Premier geste vert ».', '/achievements/', '2026-10-24 20:32:43.278894', 1, 1),
(34, 'badge_unlocked', 'Amina Ben Salah a débloqué le badge « Champion d’équipe ».', '/achievements/', '2026-10-24 20:32:43.300259', 1, 1),
(35, 'badge_unlocked', 'Nour Belhadj a débloqué le badge « Champion d’équipe ».', '/achievements/', '2026-10-24 20:32:43.370191', 3, 1),
(36, 'badge_unlocked', 'Youssef Trabelsi a débloqué le badge « Champion d’équipe ».', '/achievements/', '2026-10-24 20:32:43.407536', 2, 1),
(37, 'action_submitted', 'Lina Haddad a déclaré l’action « Tri sélectif des déchets ».', '/actions/2/', '2026-10-13 17:21:00.000000', 4, 2),
(38, 'action_approved', 'Action validée : « Tri sélectif des déchets » (+10 pts).', '/actions/2/', '2026-10-14 10:05:00.000000', 4, 2),
(39, 'badge_unlocked', 'Lina Haddad a débloqué le badge « Premier geste vert ».', '/achievements/', '2026-10-24 20:32:43.554426', 4, 2),
(40, 'badge_unlocked', 'Lina Haddad a débloqué le badge « Champion d’équipe ».', '/achievements/', '2026-10-24 20:32:43.569274', 4, 2),
(41, 'badge_unlocked', 'Karim Jaziri a débloqué le badge « Champion d’équipe ».', '/achievements/', '2026-10-24 20:32:43.623097', 5, 2),
(42, 'action_submitted', 'Amina Ben Salah a déclaré l’action « Transports en commun plutôt que la voiture ».', '/actions/3/', '2026-10-14 17:35:00.000000', 1, 1),
(43, 'action_approved', 'Action validée : « Transports en commun plutôt que la voiture » (+10 pts).', '/actions/3/', '2026-10-15 10:34:00.000000', 1, 1),
(44, 'action_submitted', 'Youssef Trabelsi a déclaré l’action « Lutte contre le gaspillage alimentaire ».', '/actions/4/', '2026-10-15 17:18:00.000000', 2, 1),
(45, 'action_approved', 'Action validée : « Lutte contre le gaspillage alimentaire » (+10 pts).', '/actions/4/', '2026-10-16 10:18:00.000000', 2, 1),
(46, 'badge_unlocked', 'Youssef Trabelsi a débloqué le badge « Premier geste vert ».', '/achievements/', '2026-10-24 20:32:43.868025', 2, 1),
(47, 'action_submitted', 'Karim Jaziri a déclaré l’action « Gourde et contenants réutilisables ».', '/actions/5/', '2026-10-15 17:29:00.000000', 5, 2),
(48, 'action_approved', 'Action validée : « Gourde et contenants réutilisables » (+5 pts).', '/actions/5/', '2026-10-16 10:09:00.000000', 5, 2),
(49, 'badge_unlocked', 'Karim Jaziri a débloqué le badge « Premier geste vert ».', '/achievements/', '2026-10-24 20:32:44.098115', 5, 2),
(50, 'action_submitted', 'Sarra Mansour a déclaré l’action « Lessive à basse température ».', '/actions/6/', '2026-10-15 17:56:00.000000', 6, 3),
(51, 'action_approved', 'Action validée : « Lessive à basse température » (+6 pts).', '/actions/6/', '2026-10-16 10:41:00.000000', 6, 3),
(52, 'badge_unlocked', 'Sarra Mansour a débloqué le badge « Premier geste vert ».', '/achievements/', '2026-10-24 20:32:44.231525', 6, 3),
(53, 'action_submitted', 'Amina Ben Salah a déclaré l’action « Trajet à vélo ou à pied ».', '/actions/7/', '2026-10-16 17:45:00.000000', 1, 1),
(54, 'action_approved', 'Action validée : « Trajet à vélo ou à pied » (+15 pts).', '/actions/7/', '2026-10-17 10:45:00.000000', 1, 1),
(55, 'action_submitted', 'Lina Haddad a déclaré l’action « Tri sélectif des déchets ».', '/actions/8/', '2026-10-16 17:36:00.000000', 4, 2),
(56, 'action_approved', 'Action validée : « Tri sélectif des déchets » (+10 pts).', '/actions/8/', '2026-10-17 10:19:00.000000', 4, 2),
(57, 'action_submitted', 'Omar Ferchichi a déclaré l’action « Récupération d’eau de pluie ».', '/actions/9/', '2026-10-16 17:01:00.000000', 9, 4),
(58, 'action_approved', 'Action validée : « Récupération d’eau de pluie » (+12 pts).', '/actions/9/', '2026-10-17 10:54:00.000000', 9, 4),
(59, 'badge_unlocked', 'Omar Ferchichi a débloqué le badge « Premier geste vert ».', '/achievements/', '2026-10-24 20:32:44.633701', 9, 4),
(60, 'action_submitted', 'Amina Ben Salah a déclaré l’action « Trajet à vélo ou à pied ».', '/actions/10/', '2026-10-17 17:45:00.000000', 1, 1),
(61, 'action_approved', 'Action validée : « Trajet à vélo ou à pied » (+15 pts).', '/actions/10/', '2026-10-18 10:23:00.000000', 1, 1),
(62, 'badge_unlocked', 'Amina Ben Salah a débloqué le badge « Éco-débutant ».', '/achievements/', '2026-10-24 20:32:44.744579', 1, 1),
(63, 'action_submitted', 'Nour Belhadj a déclaré l’action « Repas végétarien ».', '/actions/11/', '2026-10-17 17:23:00.000000', 3, 1),
(64, 'action_approved', 'Action validée : « Repas végétarien » (+8 pts).', '/actions/11/', '2026-10-18 10:29:00.000000', 3, 1),
(65, 'badge_unlocked', 'Nour Belhadj a débloqué le badge « Premier geste vert ».', '/achievements/', '2026-10-24 20:32:44.893252', 3, 1),
(66, 'action_submitted', 'Lina Haddad a déclaré l’action « Réparer au lieu de jeter ».', '/actions/12/', '2026-10-17 17:27:00.000000', 4, 2),
(67, 'action_approved', 'Action validée : « Réparer au lieu de jeter » (+20 pts).', '/actions/12/', '2026-10-18 10:05:00.000000', 4, 2),
(68, 'action_submitted', 'Sarra Mansour a déclaré l’action « Éteindre les appareils en veille ».', '/actions/13/', '2026-10-17 17:25:00.000000', 6, 3),
(69, 'action_approved', 'Action validée : « Éteindre les appareils en veille » (+8 pts).', '/actions/13/', '2026-10-18 10:57:00.000000', 6, 3),
(70, 'action_submitted', 'Amina Ben Salah a déclaré l’action « Trajet à vélo ou à pied ».', '/actions/14/', '2026-10-18 17:37:00.000000', 1, 1),
(71, 'action_approved', 'Action validée : « Trajet à vélo ou à pied » (+15 pts).', '/actions/14/', '2026-10-19 10:35:00.000000', 1, 1),
(72, 'badge_unlocked', 'Amina Ben Salah a débloqué le badge « Cycliste urbain ».', '/achievements/', '2026-10-24 20:32:45.310174', 1, 1),
(73, 'action_submitted', 'Youssef Trabelsi a déclaré l’action « Trajet à vélo ou à pied ».', '/actions/15/', '2026-10-18 17:31:00.000000', 2, 1),
(74, 'action_approved', 'Action validée : « Trajet à vélo ou à pied » (+15 pts).', '/actions/15/', '2026-10-19 10:55:00.000000', 2, 1),
(75, 'action_submitted', 'Lina Haddad a déclaré l’action « Tri sélectif des déchets ».', '/actions/16/', '2026-10-18 17:07:00.000000', 4, 2),
(76, 'action_approved', 'Action validée : « Tri sélectif des déchets » (+10 pts).', '/actions/16/', '2026-10-19 10:27:00.000000', 4, 2),
(77, 'badge_unlocked', 'Lina Haddad a débloqué le badge « Éco-débutant ».', '/achievements/', '2026-10-24 20:32:45.680521', 4, 2),
(78, 'action_submitted', 'Karim Jaziri a déclaré l’action « Éteindre les appareils en veille ».', '/actions/17/', '2026-10-18 17:32:00.000000', 5, 2),
(79, 'action_approved', 'Action validée : « Éteindre les appareils en veille » (+8 pts).', '/actions/17/', '2026-10-19 10:51:00.000000', 5, 2),
(80, 'action_submitted', 'Mehdi Gharbi a déclaré l’action « Covoiturage ».', '/actions/18/', '2026-10-18 17:48:00.000000', 7, 3),
(81, 'action_approved', 'Action validée : « Covoiturage » (+8 pts).', '/actions/18/', '2026-10-19 10:55:00.000000', 7, 3),
(82, 'badge_unlocked', 'Mehdi Gharbi a débloqué le badge « Premier geste vert ».', '/achievements/', '2026-10-24 20:32:45.934094', 7, 3),
(83, 'action_submitted', 'Omar Ferchichi a déclaré l’action « Douche de moins de 5 minutes ».', '/actions/19/', '2026-10-18 17:38:00.000000', 9, 4),
(84, 'action_approved', 'Action validée : « Douche de moins de 5 minutes » (+6 pts).', '/actions/19/', '2026-10-19 10:56:00.000000', 9, 4),
(85, 'action_submitted', 'Amina Ben Salah a déclaré l’action « Trajet à vélo ou à pied ».', '/actions/20/', '2026-10-19 17:31:00.000000', 1, 1),
(86, 'action_approved', 'Action validée : « Trajet à vélo ou à pied » (+15 pts).', '/actions/20/', '2026-10-20 10:25:00.000000', 1, 1),
(87, 'action_submitted', 'Youssef Trabelsi a déclaré l’action « Repas végétarien ».', '/actions/21/', '2026-10-19 17:58:00.000000', 2, 1),
(88, 'action_approved', 'Action validée : « Repas végétarien » (+8 pts).', '/actions/21/', '2026-10-20 10:33:00.000000', 2, 1),
(89, 'action_submitted', 'Nour Belhadj a déclaré l’action « Transports en commun plutôt que la voiture ».', '/actions/22/', '2026-10-19 17:16:00.000000', 3, 1),
(90, 'action_approved', 'Action validée : « Transports en commun plutôt que la voiture » (+10 pts).', '/actions/22/', '2026-10-20 10:54:00.000000', 3, 1),
(91, 'action_submitted', 'Karim Jaziri a déclaré l’action « Tri sélectif des déchets ».', '/actions/23/', '2026-10-19 17:26:00.000000', 5, 2),
(92, 'action_approved', 'Action validée : « Tri sélectif des déchets » (+10 pts).', '/actions/23/', '2026-10-20 10:36:00.000000', 5, 2),
(93, 'action_submitted', 'Sarra Mansour a déclaré l’action « Éteindre les appareils en veille ».', '/actions/24/', '2026-10-19 17:59:00.000000', 6, 3),
(94, 'action_approved', 'Action validée : « Éteindre les appareils en veille » (+8 pts).', '/actions/24/', '2026-10-20 10:30:00.000000', 6, 3),
(95, 'action_submitted', 'Inès Chaabane a déclaré l’action « Éteindre les appareils en veille ».', '/actions/25/', '2026-10-19 17:32:00.000000', 8, 3),
(96, 'action_approved', 'Action validée : « Éteindre les appareils en veille » (+8 pts).', '/actions/25/', '2026-10-20 10:33:00.000000', 8, 3),
(97, 'badge_unlocked', 'Inès Chaabane a débloqué le badge « Premier geste vert ».', '/achievements/', '2026-10-24 20:32:46.862325', 8, 3),
(98, 'action_submitted', 'Omar Ferchichi a déclaré l’action « Douche de moins de 5 minutes ».', '/actions/26/', '2026-10-19 17:51:00.000000', 9, 4),
(99, 'action_approved', 'Action validée : « Douche de moins de 5 minutes » (+6 pts).', '/actions/26/', '2026-10-20 10:01:00.000000', 9, 4),
(100, 'action_submitted', 'Amina Ben Salah a déclaré l’action « Trajet à vélo ou à pied ».', '/actions/27/', '2026-10-20 17:36:00.000000', 1, 1),
(101, 'action_approved', 'Action validée : « Trajet à vélo ou à pied » (+15 pts).', '/actions/27/', '2026-10-21 10:14:00.000000', 1, 1),
(102, 'action_submitted', 'Youssef Trabelsi a déclaré l’action « Trajet à vélo ou à pied ».', '/actions/28/', '2026-10-20 17:49:00.000000', 2, 1),
(103, 'action_approved', 'Action validée : « Trajet à vélo ou à pied » (+15 pts).', '/actions/28/', '2026-10-21 10:08:00.000000', 2, 1),
(104, 'action_submitted', 'Nour Belhadj a déclaré l’action « Douche de moins de 5 minutes ».', '/actions/29/', '2026-10-20 17:52:00.000000', 3, 1),
(105, 'action_approved', 'Action validée : « Douche de moins de 5 minutes » (+6 pts).', '/actions/29/', '2026-10-21 10:03:00.000000', 3, 1),
(106, 'action_submitted', 'Lina Haddad a déclaré l’action « Tri sélectif des déchets ».', '/actions/30/', '2026-10-20 17:45:00.000000', 4, 2),
(107, 'action_approved', 'Action validée : « Tri sélectif des déchets » (+10 pts).', '/actions/30/', '2026-10-21 10:33:00.000000', 4, 2),
(108, 'action_submitted', 'Sarra Mansour a déclaré l’action « Lessive à basse température ».', '/actions/31/', '2026-10-20 17:56:00.000000', 6, 3),
(109, 'action_approved', 'Action validée : « Lessive à basse température » (+6 pts).', '/actions/31/', '2026-10-21 10:42:00.000000', 6, 3),
(110, 'action_submitted', 'Mehdi Gharbi a déclaré l’action « Éteindre les appareils en veille ».', '/actions/32/', '2026-10-20 17:06:00.000000', 7, 3),
(111, 'action_approved', 'Action validée : « Éteindre les appareils en veille » (+8 pts).', '/actions/32/', '2026-10-21 10:45:00.000000', 7, 3),
(112, 'action_submitted', 'Omar Ferchichi a déclaré l’action « Douche de moins de 5 minutes ».', '/actions/33/', '2026-10-20 17:39:00.000000', 9, 4),
(113, 'action_approved', 'Action validée : « Douche de moins de 5 minutes » (+6 pts).', '/actions/33/', '2026-10-21 10:27:00.000000', 9, 4),
(114, 'action_submitted', 'Amina Ben Salah a déclaré l’action « Trajet à vélo ou à pied ».', '/actions/34/', '2026-10-21 17:30:00.000000', 1, 1),
(115, 'action_approved', 'Action validée : « Trajet à vélo ou à pied » (+15 pts).', '/actions/34/', '2026-10-22 10:09:00.000000', 1, 1),
(116, 'action_submitted', 'Youssef Trabelsi a déclaré l’action « Trajet à vélo ou à pied ».', '/actions/35/', '2026-10-21 17:30:00.000000', 2, 1),
(117, 'action_approved', 'Action validée : « Trajet à vélo ou à pied » (+15 pts).', '/actions/35/', '2026-10-22 10:56:00.000000', 2, 1),
(118, 'badge_unlocked', 'Youssef Trabelsi a débloqué le badge « Éco-débutant ».', '/achievements/', '2026-10-24 20:32:48.080386', 2, 1),
(119, 'action_submitted', 'Nour Belhadj a déclaré l’action « Douche de moins de 5 minutes ».', '/actions/36/', '2026-10-21 17:14:00.000000', 3, 1),
(120, 'action_approved', 'Action validée : « Douche de moins de 5 minutes » (+6 pts).', '/actions/36/', '2026-10-22 10:54:00.000000', 3, 1),
(121, 'action_submitted', 'Lina Haddad a déclaré l’action « Gourde et contenants réutilisables ».', '/actions/37/', '2026-10-21 17:56:00.000000', 4, 2),
(122, 'action_approved', 'Action validée : « Gourde et contenants réutilisables » (+5 pts).', '/actions/37/', '2026-10-22 10:07:00.000000', 4, 2),
(123, 'action_submitted', 'Sarra Mansour a déclaré l’action « Éteindre les appareils en veille ».', '/actions/38/', '2026-10-21 17:40:00.000000', 6, 3),
(124, 'action_approved', 'Action validée : « Éteindre les appareils en veille » (+8 pts).', '/actions/38/', '2026-10-22 10:44:00.000000', 6, 3),
(125, 'badge_unlocked', 'Sarra Mansour a débloqué le badge « Économe en énergie ».', '/achievements/', '2026-10-24 20:32:48.447794', 6, 3),
(126, 'action_submitted', 'Inès Chaabane a déclaré l’action « Douche de moins de 5 minutes ».', '/actions/39/', '2026-10-21 17:29:00.000000', 8, 3),
(127, 'action_approved', 'Action validée : « Douche de moins de 5 minutes » (+6 pts).', '/actions/39/', '2026-10-22 10:43:00.000000', 8, 3),
(128, 'action_submitted', 'Omar Ferchichi a déclaré l’action « Douche de moins de 5 minutes ».', '/actions/40/', '2026-10-21 17:30:00.000000', 9, 4),
(129, 'action_approved', 'Action validée : « Douche de moins de 5 minutes » (+6 pts).', '/actions/40/', '2026-10-22 10:45:00.000000', 9, 4),
(130, 'action_submitted', 'Amina Ben Salah a déclaré l’action « Trajet à vélo ou à pied ».', '/actions/41/', '2026-10-22 17:59:00.000000', 1, 1),
(131, 'action_approved', 'Action validée : « Trajet à vélo ou à pied » (+15 pts).', '/actions/41/', '2026-10-23 10:34:00.000000', 1, 1),
(132, 'badge_unlocked', 'Amina Ben Salah a débloqué le badge « Série de 7 jours ».', '/achievements/', '2026-10-24 20:32:49.000526', 1, 1),
(133, 'action_submitted', 'Nour Belhadj a déclaré l’action « Transports en commun plutôt que la voiture ».', '/actions/42/', '2026-10-22 17:16:00.000000', 3, 1),
(134, 'action_approved', 'Action validée : « Transports en commun plutôt que la voiture » (+10 pts).', '/actions/42/', '2026-10-23 10:35:00.000000', 3, 1),
(135, 'action_submitted', 'Lina Haddad a déclaré l’action « Tri sélectif des déchets ».', '/actions/43/', '2026-10-22 17:25:00.000000', 4, 2),
(136, 'action_approved', 'Action validée : « Tri sélectif des déchets » (+10 pts).', '/actions/43/', '2026-10-23 10:42:00.000000', 4, 2),
(137, 'badge_unlocked', 'Lina Haddad a débloqué le badge « Héros du recyclage ».', '/achievements/', '2026-10-24 20:32:49.292415', 4, 2),
(138, 'action_submitted', 'Karim Jaziri a déclaré l’action « Tri sélectif des déchets ».', '/actions/44/', '2026-10-22 17:19:00.000000', 5, 2),
(139, 'action_approved', 'Action validée : « Tri sélectif des déchets » (+10 pts).', '/actions/44/', '2026-10-23 10:35:00.000000', 5, 2),
(140, 'action_submitted', 'Sarra Mansour a déclaré l’action « Éteindre les appareils en veille ».', '/actions/45/', '2026-10-22 17:51:00.000000', 6, 3),
(141, 'action_approved', 'Action validée : « Éteindre les appareils en veille » (+8 pts).', '/actions/45/', '2026-10-23 10:41:00.000000', 6, 3),
(142, 'action_submitted', 'Mehdi Gharbi a déclaré l’action « Éteindre les appareils en veille ».', '/actions/46/', '2026-10-22 17:32:00.000000', 7, 3),
(143, 'action_approved', 'Action validée : « Éteindre les appareils en veille » (+8 pts).', '/actions/46/', '2026-10-23 10:44:00.000000', 7, 3),
(144, 'action_submitted', 'Inès Chaabane a déclaré l’action « Douche de moins de 5 minutes ».', '/actions/47/', '2026-10-22 17:30:00.000000', 8, 3),
(145, 'action_approved', 'Action validée : « Douche de moins de 5 minutes » (+6 pts).', '/actions/47/', '2026-10-23 10:51:00.000000', 8, 3),
(146, 'action_submitted', 'Omar Ferchichi a déclaré l’action « Douche de moins de 5 minutes ».', '/actions/48/', '2026-10-22 17:56:00.000000', 9, 4),
(147, 'action_approved', 'Action validée : « Douche de moins de 5 minutes » (+6 pts).', '/actions/48/', '2026-10-23 10:25:00.000000', 9, 4),
(148, 'action_submitted', 'Amina Ben Salah a déclaré l’action « Trajet à vélo ou à pied ».', '/actions/49/', '2026-10-23 17:27:00.000000', 1, 1),
(149, 'action_approved', 'Action validée : « Trajet à vélo ou à pied » (+15 pts).', '/actions/49/', '2026-10-24 10:12:00.000000', 1, 1),
(150, 'action_submitted', 'Lina Haddad a déclaré l’action « Tri sélectif des déchets ».', '/actions/50/', '2026-10-23 17:18:00.000000', 4, 2),
(151, 'action_approved', 'Action validée : « Tri sélectif des déchets » (+10 pts).', '/actions/50/', '2026-10-24 10:53:00.000000', 4, 2),
(152, 'action_submitted', 'Sarra Mansour a déclaré l’action « Éteindre les appareils en veille ».', '/actions/51/', '2026-10-23 17:17:00.000000', 6, 3),
(153, 'action_approved', 'Action validée : « Éteindre les appareils en veille » (+8 pts).', '/actions/51/', '2026-10-24 10:00:00.000000', 6, 3),
(154, 'badge_unlocked', 'Sarra Mansour a débloqué le badge « Éco-débutant ».', '/achievements/', '2026-10-24 20:32:50.350466', 6, 3),
(155, 'action_submitted', 'Inès Chaabane a déclaré l’action « Douche de moins de 5 minutes ».', '/actions/52/', '2026-10-23 17:02:00.000000', 8, 3),
(156, 'action_approved', 'Action validée : « Douche de moins de 5 minutes » (+6 pts).', '/actions/52/', '2026-10-24 10:09:00.000000', 8, 3),
(157, 'action_submitted', 'Omar Ferchichi a déclaré l’action « Douche de moins de 5 minutes ».', '/actions/53/', '2026-10-23 17:41:00.000000', 9, 4),
(158, 'action_approved', 'Action validée : « Douche de moins de 5 minutes » (+6 pts).', '/actions/53/', '2026-10-24 10:56:00.000000', 9, 4),
(159, 'action_submitted', 'Amina Ben Salah a déclaré l’action « Transports en commun plutôt que la voiture ».', '/actions/54/', '2026-10-24 17:38:00.000000', 1, 1),
(160, 'action_submitted', 'Karim Jaziri a déclaré l’action « Tri sélectif des déchets ».', '/actions/55/', '2026-10-24 17:29:00.000000', 5, 2),
(161, 'action_submitted', 'Mehdi Gharbi a déclaré l’action « Éteindre les appareils en veille ».', '/actions/56/', '2026-10-23 17:51:00.000000', 7, 3),
(162, 'action_submitted', 'Inès Chaabane a déclaré l’action « Lutte contre le gaspillage alimentaire ».', '/actions/57/', '2026-10-23 17:33:00.000000', 8, 3),
(163, 'action_submitted', 'Youssef Trabelsi a déclaré l’action « Réparer au lieu de jeter ».', '/actions/58/', '2026-10-22 17:59:00.000000', 2, 1),
(164, 'action_rejected', 'Action refusée : « Réparer au lieu de jeter ».', '/actions/58/', '2026-10-24 20:32:50.699178', 2, 1),
(165, 'challenge_completed', 'Omar Ferchichi a réussi le défi « Douches express ».', '/challenges/douches-express/', '2026-10-24 20:32:50.766139', 9, 4),
(166, 'badge_unlocked', 'Omar Ferchichi a débloqué le badge « Défi relevé ».', '/achievements/', '2026-10-24 20:32:50.812990', 9, 4),
(167, 'badge_unlocked', 'Omar Ferchichi a débloqué le badge « Éco-débutant ».', '/achievements/', '2026-10-24 20:32:50.822781', 9, 4),
(168, 'challenge_completed', 'Sarra Mansour a réussi le défi « Chasse au gaspillage énergétique ».', '/challenges/chasse-au-gaspillage-energetique/', '2026-10-24 20:32:50.909832', 6, 3),
(169, 'badge_unlocked', 'Sarra Mansour a débloqué le badge « Défi relevé ».', '/achievements/', '2026-10-24 20:32:50.984401', 6, 3),
(170, 'challenge_completed', 'Lina Haddad a réussi le défi « Tri sélectif au quotidien ».', '/challenges/tri-selectif-au-quotidien/', '2026-10-24 20:32:51.030445', 4, 2),
(171, 'badge_unlocked', 'Lina Haddad a débloqué le badge « Défi relevé ».', '/achievements/', '2026-10-24 20:32:51.067516', 4, 2),
(172, 'challenge_completed', 'Amina Ben Salah a réussi le défi « Mois du vélo ».', '/challenges/mois-du-velo/', '2026-10-24 20:32:51.130971', 1, 1),
(173, 'badge_unlocked', 'Amina Ben Salah a débloqué le badge « Défi relevé ».', '/achievements/', '2026-10-24 20:32:51.175628', 1, 1),
(174, 'challenge_completed', 'Youssef Trabelsi a réussi le défi « Mois du vélo ».', '/challenges/mois-du-velo/', '2026-10-24 20:32:51.249454', 2, 1),
(175, 'badge_unlocked', 'Youssef Trabelsi a débloqué le badge « Défi relevé ».', '/achievements/', '2026-10-24 20:32:51.300888', 2, 1),
(176, 'goal_created', 'Amina Ben Salah s’est fixé l’objectif « 15 trajets à vélo ce mois-ci ».', '/goals/1/', '2026-10-04 09:44:00.000000', 1, NULL),
(177, 'goal_created', 'Amina Ben Salah s’est fixé l’objectif « Atteindre 200 points ».', '/goals/2/', '2026-09-29 09:31:00.000000', 1, NULL),
(178, 'goal_completed', 'Amina Ben Salah a atteint son objectif « Atteindre 200 points ».', '/goals/2/', '2026-10-24 20:32:51.505850', 1, 1),
(179, 'goal_created', 'Lina Haddad s’est fixé l’objectif « Trier chaque semaine ».', '/goals/3/', '2026-10-04 09:29:00.000000', 4, NULL),
(180, 'goal_completed', 'Lina Haddad a atteint son objectif « Trier chaque semaine ».', '/goals/3/', '2026-10-24 20:32:51.540700', 4, 2),
(181, 'goal_created', 'Sarra Mansour s’est fixé l’objectif « Réduire les veilles à zéro ».', '/goals/4/', '2026-10-09 09:32:00.000000', 6, NULL),
(182, 'goal_created', 'Omar Ferchichi s’est fixé l’objectif « Économiser 1 000 litres d’eau ».', '/goals/5/', '2026-10-14 09:49:00.000000', 9, NULL),
(183, 'goal_created', 'Youssef Trabelsi s’est fixé l’objectif « Cuisiner 5 repas anti-gaspi ».', '/goals/6/', '2026-10-19 09:52:00.000000', 2, NULL),
(184, 'goal_created', 'Nour Belhadj s’est fixé l’objectif « Prendre les transports en commun 10 fois ».', '/goals/7/', '2026-10-12 09:31:00.000000', 3, NULL),
(185, 'goal_created', 'Karim Jaziri s’est fixé l’objectif « Trier 5 fois ce mois-ci ».', '/goals/8/', '2026-10-06 09:51:00.000000', 5, NULL),
(186, 'goal_created', 'Mehdi Gharbi s’est fixé l’objectif « Atteindre 150 points ».', '/goals/9/', '2026-10-04 09:27:00.000000', 7, NULL),
(187, 'goal_created', 'Inès Chaabane s’est fixé l’objectif « Douches courtes 8 fois ».', '/goals/10/', '2026-10-10 09:35:00.000000', 8, NULL),
(188, 'goal_created', 'Youssef Trabelsi s’est fixé l’objectif « Covoiturer 3 fois ».', '/goals/11/', '2026-10-16 09:42:00.000000', 2, NULL),
(189, 'goal_completed', 'Youssef Trabelsi a atteint son objectif « Covoiturer 3 fois ».', '/goals/11/', '2026-10-24 20:32:51.698111', 2, 1),
(190, 'goal_created', 'Karim Jaziri s’est fixé l’objectif « Réparer 2 objets au lieu de jeter ».', '/goals/12/', '2026-10-19 09:58:00.000000', 5, NULL),
(191, 'goal_created', 'Sarra Mansour s’est fixé l’objectif « Atteindre 300 points ».', '/goals/13/', '2026-10-02 09:02:00.000000', 6, NULL),
(192, 'goal_created', 'Salma Ayari s’est fixé l’objectif « Donner une seconde vie à 2 objets ».', '/goals/14/', '2026-10-14 09:53:00.000000', 10, NULL),
(193, 'goal_created', 'Omar Ferchichi s’est fixé l’objectif « Prendre les transports en commun 6 fois ».', '/goals/15/', '2026-10-15 09:18:00.000000', 9, NULL),
(194, 'event_published', '« Grand nettoyage de la plage » est publié.', '/community/grand-nettoyage-de-la-plage/', '2026-10-24 20:32:51.809571', 10, NULL),
(195, 'event_published', '« Conférence : sobriété énergétique au bureau » est publié.', '/community/conference-sobriete-energetique-au-bureau/', '2026-10-24 20:32:51.846540', 10, NULL),
(196, 'event_published', '« Atelier compost urbain » est publié.', '/community/atelier-compost-urbain/', '2026-10-24 20:32:51.873244', 10, NULL),
(197, 'event_published', '« Campagne Mobilité douce » est publié.', '/community/campagne-mobilite-douce/', '2026-10-24 20:32:51.902712', 10, NULL),
(198, 'event_joined', 'Amina Ben Salah participe à « Grand nettoyage de la plage ».', '/community/grand-nettoyage-de-la-plage/', '2026-10-24 20:32:51.937107', 1, 1),
(199, 'badge_unlocked', 'Amina Ben Salah a débloqué le badge « Objectif atteint ».', '/achievements/', '2026-10-24 20:32:51.966186', 1, 1),
(200, 'event_joined', 'Lina Haddad participe à « Grand nettoyage de la plage ».', '/community/grand-nettoyage-de-la-plage/', '2026-10-24 20:32:51.981249', 4, 2),
(201, 'badge_unlocked', 'Lina Haddad a débloqué le badge « Objectif atteint ».', '/achievements/', '2026-10-24 20:32:52.008226', 4, 2),
(202, 'event_joined', 'Karim Jaziri participe à « Grand nettoyage de la plage ».', '/community/grand-nettoyage-de-la-plage/', '2026-10-24 20:32:52.021572', 5, 2),
(203, 'event_joined', 'Omar Ferchichi participe à « Grand nettoyage de la plage ».', '/community/grand-nettoyage-de-la-plage/', '2026-10-24 20:32:52.041970', 9, 4),
(204, 'event_joined', 'Nour Belhadj participe à « Grand nettoyage de la plage ».', '/community/grand-nettoyage-de-la-plage/', '2026-10-24 20:32:52.088736', 3, 1),
(205, 'event_joined', 'Sarra Mansour participe à « Conférence : sobriété énergétique au bureau ».', '/community/conference-sobriete-energetique-au-bureau/', '2026-10-24 20:32:52.125335', 6, 3),
(206, 'event_joined', 'Mehdi Gharbi participe à « Conférence : sobriété énergétique au bureau ».', '/community/conference-sobriete-energetique-au-bureau/', '2026-10-24 20:32:52.165658', 7, 3),
(207, 'event_joined', 'Inès Chaabane participe à « Conférence : sobriété énergétique au bureau ».', '/community/conference-sobriete-energetique-au-bureau/', '2026-10-24 20:32:52.211788', 8, 3),
(208, 'event_joined', 'Lina Haddad participe à « Conférence : sobriété énergétique au bureau ».', '/community/conference-sobriete-energetique-au-bureau/', '2026-10-24 20:32:52.252745', 4, 2),
(209, 'badge_unlocked', 'Lina Haddad a débloqué le badge « Citoyen engagé ».', '/achievements/', '2026-10-24 20:32:52.279295', 4, 2),
(210, 'event_joined', 'Amina Ben Salah participe à « Conférence : sobriété énergétique au bureau ».', '/community/conference-sobriete-energetique-au-bureau/', '2026-10-24 20:32:52.292769', 1, 1),
(211, 'badge_unlocked', 'Amina Ben Salah a débloqué le badge « Citoyen engagé ».', '/achievements/', '2026-10-24 20:32:52.320075', 1, 1),
(212, 'event_joined', 'Omar Ferchichi participe à « Atelier compost urbain ».', '/community/atelier-compost-urbain/', '2026-10-24 20:32:52.338832', 9, 4),
(213, 'badge_unlocked', 'Omar Ferchichi a débloqué le badge « Citoyen engagé ».', '/achievements/', '2026-10-24 20:32:52.373072', 9, 4),
(214, 'event_joined', 'Youssef Trabelsi participe à « Atelier compost urbain ».', '/community/atelier-compost-urbain/', '2026-10-24 20:32:52.386819', 2, 1),
(215, 'badge_unlocked', 'Youssef Trabelsi a débloqué le badge « Objectif atteint ».', '/achievements/', '2026-10-24 20:32:52.425220', 2, 1),
(216, 'event_joined', 'Amina Ben Salah participe à « Campagne Mobilité douce ».', '/community/campagne-mobilite-douce/', '2026-10-24 20:32:52.441215', 1, 1),
(217, 'event_joined', 'Youssef Trabelsi participe à « Campagne Mobilité douce ».', '/community/campagne-mobilite-douce/', '2026-10-24 20:32:52.469445', 2, 1),
(218, 'badge_unlocked', 'Youssef Trabelsi a débloqué le badge « Citoyen engagé ».', '/achievements/', '2026-10-24 20:32:52.506483', 2, 1),
(219, 'event_joined', 'Nour Belhadj participe à « Campagne Mobilité douce ».', '/community/campagne-mobilite-douce/', '2026-10-24 20:32:52.524440', 3, 1),
(220, 'badge_unlocked', 'Nour Belhadj a débloqué le badge « Citoyen engagé ».', '/achievements/', '2026-10-24 20:32:52.601711', 3, 1),
(221, 'event_joined', 'Mehdi Gharbi participe à « Campagne Mobilité douce ».', '/community/campagne-mobilite-douce/', '2026-10-24 20:32:52.628840', 7, 3),
(222, 'badge_unlocked', 'Mehdi Gharbi a débloqué le badge « Citoyen engagé ».', '/achievements/', '2026-10-24 20:32:52.683420', 7, 3),
(223, 'challenge_joined', 'Amina Ben Salah relève le défi « Chasse au gaspillage énergétique ».', '/challenges/chasse-au-gaspillage-energetique/', '2026-10-24 21:02:38.755889', 1, 1);

-- --------------------------------------------------------

--
-- Structure de la table `auth_group`
--

CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL,
  `name` varchar(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `auth_group`
--

INSERT INTO `auth_group` (`id`, `name`) VALUES
(2, 'Modérateur'),
(1, 'Utilisateur');

-- --------------------------------------------------------

--
-- Structure de la table `auth_group_permissions`
--

CREATE TABLE `auth_group_permissions` (
  `id` bigint(20) NOT NULL,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `auth_group_permissions`
--

INSERT INTO `auth_group_permissions` (`id`, `group_id`, `permission_id`) VALUES
(2, 2, 41),
(1, 2, 54),
(3, 2, 80),
(4, 2, 97);

-- --------------------------------------------------------

--
-- Structure de la table `auth_permission`
--

CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `auth_permission`
--

INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES
(1, 'Can add log entry', 1, 'add_logentry'),
(2, 'Can change log entry', 1, 'change_logentry'),
(3, 'Can delete log entry', 1, 'delete_logentry'),
(4, 'Can view log entry', 1, 'view_logentry'),
(5, 'Can add permission', 2, 'add_permission'),
(6, 'Can change permission', 2, 'change_permission'),
(7, 'Can delete permission', 2, 'delete_permission'),
(8, 'Can view permission', 2, 'view_permission'),
(9, 'Can add group', 3, 'add_group'),
(10, 'Can change group', 3, 'change_group'),
(11, 'Can delete group', 3, 'delete_group'),
(12, 'Can view group', 3, 'view_group'),
(13, 'Can add content type', 4, 'add_contenttype'),
(14, 'Can change content type', 4, 'change_contenttype'),
(15, 'Can delete content type', 4, 'delete_contenttype'),
(16, 'Can view content type', 4, 'view_contenttype'),
(17, 'Can add session', 5, 'add_session'),
(18, 'Can change session', 5, 'change_session'),
(19, 'Can delete session', 5, 'delete_session'),
(20, 'Can view session', 5, 'view_session'),
(21, 'Can add utilisateur', 6, 'add_user'),
(22, 'Can change utilisateur', 6, 'change_user'),
(23, 'Can delete utilisateur', 6, 'delete_user'),
(24, 'Can view utilisateur', 6, 'view_user'),
(25, 'Can add rôle', 7, 'add_role'),
(26, 'Can change rôle', 7, 'change_role'),
(27, 'Can delete rôle', 7, 'delete_role'),
(28, 'Can view rôle', 7, 'view_role'),
(29, 'Can add adhésion', 8, 'add_membership'),
(30, 'Can change adhésion', 8, 'change_membership'),
(31, 'Can delete adhésion', 8, 'delete_membership'),
(32, 'Can view adhésion', 8, 'view_membership'),
(33, 'Can add équipe', 9, 'add_team'),
(34, 'Can change équipe', 9, 'change_team'),
(35, 'Can delete équipe', 9, 'delete_team'),
(36, 'Can view équipe', 9, 'view_team'),
(37, 'Can add défi', 10, 'add_challenge'),
(38, 'Can change défi', 10, 'change_challenge'),
(39, 'Can delete défi', 10, 'delete_challenge'),
(40, 'Can view défi', 10, 'view_challenge'),
(41, 'Peut valider, publier et clôturer les défis', 10, 'review_challenge'),
(42, 'Can add participation à un défi', 11, 'add_challengeparticipation'),
(43, 'Can change participation à un défi', 11, 'change_challengeparticipation'),
(44, 'Can delete participation à un défi', 11, 'delete_challengeparticipation'),
(45, 'Can view participation à un défi', 11, 'view_challengeparticipation'),
(46, 'Can add type d’action écologique', 12, 'add_ecoactiontype'),
(47, 'Can change type d’action écologique', 12, 'change_ecoactiontype'),
(48, 'Can delete type d’action écologique', 12, 'delete_ecoactiontype'),
(49, 'Can view type d’action écologique', 12, 'view_ecoactiontype'),
(50, 'Can add déclaration d’action', 13, 'add_actionsubmission'),
(51, 'Can change déclaration d’action', 13, 'change_actionsubmission'),
(52, 'Can delete déclaration d’action', 13, 'delete_actionsubmission'),
(53, 'Can view déclaration d’action', 13, 'view_actionsubmission'),
(54, 'Peut modérer les déclarations d’actions', 13, 'moderate_actionsubmission'),
(55, 'Can add décision de modération', 14, 'add_moderationlog'),
(56, 'Can change décision de modération', 14, 'change_moderationlog'),
(57, 'Can delete décision de modération', 14, 'delete_moderationlog'),
(58, 'Can view décision de modération', 14, 'view_moderationlog'),
(59, 'Can add objectif personnel', 15, 'add_goal'),
(60, 'Can change objectif personnel', 15, 'change_goal'),
(61, 'Can delete objectif personnel', 15, 'delete_goal'),
(62, 'Can view objectif personnel', 15, 'view_goal'),
(63, 'Can add badge', 16, 'add_badge'),
(64, 'Can change badge', 16, 'change_badge'),
(65, 'Can delete badge', 16, 'delete_badge'),
(66, 'Can view badge', 16, 'view_badge'),
(67, 'Can add transaction de points', 17, 'add_pointtransaction'),
(68, 'Can change transaction de points', 17, 'change_pointtransaction'),
(69, 'Can delete transaction de points', 17, 'delete_pointtransaction'),
(70, 'Can view transaction de points', 17, 'view_pointtransaction'),
(71, 'Peut enregistrer des corrections de points', 17, 'adjust_points'),
(72, 'Can add badge obtenu', 18, 'add_userbadge'),
(73, 'Can change badge obtenu', 18, 'change_userbadge'),
(74, 'Can delete badge obtenu', 18, 'delete_userbadge'),
(75, 'Can view badge obtenu', 18, 'view_userbadge'),
(76, 'Can add événement ou campagne', 19, 'add_event'),
(77, 'Can change événement ou campagne', 19, 'change_event'),
(78, 'Can delete événement ou campagne', 19, 'delete_event'),
(79, 'Can view événement ou campagne', 19, 'view_event'),
(80, 'Peut valider et publier les événements', 19, 'review_event'),
(81, 'Can add participation à un événement', 20, 'add_eventparticipation'),
(82, 'Can change participation à un événement', 20, 'change_eventparticipation'),
(83, 'Can delete participation à un événement', 20, 'delete_eventparticipation'),
(84, 'Can view participation à un événement', 20, 'view_eventparticipation'),
(85, 'Can add préférence de notification', 21, 'add_notificationpreference'),
(86, 'Can change préférence de notification', 21, 'change_notificationpreference'),
(87, 'Can delete préférence de notification', 21, 'delete_notificationpreference'),
(88, 'Can view préférence de notification', 21, 'view_notificationpreference'),
(89, 'Can add notification', 22, 'add_notification'),
(90, 'Can change notification', 22, 'change_notification'),
(91, 'Can delete notification', 22, 'delete_notification'),
(92, 'Can view notification', 22, 'view_notification'),
(93, 'Can add activité', 23, 'add_activitylog'),
(94, 'Can change activité', 23, 'change_activitylog'),
(95, 'Can delete activité', 23, 'delete_activitylog'),
(96, 'Can view activité', 23, 'view_activitylog'),
(97, 'Peut consulter les rapports d’engagement', 23, 'view_reports');

-- --------------------------------------------------------

--
-- Structure de la table `challenges_challenge`
--

CREATE TABLE `challenges_challenge` (
  `id` bigint(20) NOT NULL,
  `title` varchar(120) NOT NULL,
  `slug` varchar(140) NOT NULL,
  `description` longtext NOT NULL,
  `category` varchar(20) NOT NULL,
  `difficulty` varchar(10) NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `duration_days` smallint(5) UNSIGNED NOT NULL CHECK (`duration_days` >= 0),
  `reward_points` int(10) UNSIGNED NOT NULL CHECK (`reward_points` >= 0),
  `required_actions` smallint(5) UNSIGNED NOT NULL CHECK (`required_actions` >= 0),
  `instructions` longtext NOT NULL,
  `image` varchar(100) NOT NULL,
  `status` varchar(20) NOT NULL,
  `review_notes` longtext NOT NULL,
  `published_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `creator_id` bigint(20) DEFAULT NULL,
  `reviewed_by_id` bigint(20) DEFAULT NULL
) ;

--
-- Déchargement des données de la table `challenges_challenge`
--

INSERT INTO `challenges_challenge` (`id`, `title`, `slug`, `description`, `category`, `difficulty`, `start_date`, `end_date`, `duration_days`, `reward_points`, `required_actions`, `instructions`, `image`, `status`, `review_notes`, `published_at`, `created_at`, `updated_at`, `creator_id`, `reviewed_by_id`) VALUES
(1, 'Mois du vélo', 'mois-du-velo', 'Pendant un mois, remplacez au moins trois trajets en voiture par le vélo ou la marche.', 'transport', 'medium', '2026-10-04', '2026-11-03', 30, 80, 3, 'Vérifiez votre vélo et votre éclairage\nRepérez un itinéraire sécurisé\nDéclarez chaque trajet en le liant au défi', '', 'active', 'Défi de démonstration validé.', '2026-10-04 09:06:00.000000', '2026-10-24 20:32:42.610365', '2026-10-24 20:32:42.636555', 10, 10),
(2, 'Tri sélectif au quotidien', 'tri-selectif-au-quotidien', 'Installez un tri efficace chez vous ou au bureau et tenez-le pendant deux semaines.', 'recycling', 'easy', '2026-10-09', '2026-11-08', 30, 100, 4, 'Identifiez les consignes de tri de votre commune\nÉquipez-vous de bacs séparés\nDéclarez vos actions de tri', '', 'active', 'Défi de démonstration validé.', '2026-10-09 09:28:00.000000', '2026-10-24 20:32:42.679498', '2026-10-24 20:32:42.685311', 4, 10),
(3, 'Chasse au gaspillage énergétique', 'chasse-au-gaspillage-energetique', 'Traquez les veilles inutiles et réduisez la consommation électrique de votre lieu de vie.', 'energy', 'medium', '2026-10-14', '2026-11-13', 30, 90, 3, 'Listez les appareils en veille\nInstallez des multiprises à interrupteur\nCoupez-les chaque soir et déclarez-le', '', 'active', 'Défi de démonstration validé.', '2026-10-14 09:00:00.000000', '2026-10-24 20:32:42.715098', '2026-10-24 20:32:42.722306', 6, 10),
(4, 'Douches express', 'douches-express', 'Limitez vos douches à moins de cinq minutes pendant un mois.', 'water', 'easy', '2026-10-17', '2026-11-16', 30, 70, 5, 'Utilisez un minuteur\nCoupez l’eau pendant le savonnage\nDéclarez vos douches courtes', '', 'active', 'Défi de démonstration validé.', '2026-10-17 09:52:00.000000', '2026-10-24 20:32:42.755636', '2026-10-24 20:32:42.762471', 9, 10),
(5, 'Zéro gaspillage alimentaire', 'zero-gaspillage-alimentaire', 'Un mois sans jeter de nourriture : planification, restes cuisinés, dons.', 'food', 'hard', '2026-10-26', '2026-11-25', 30, 120, 6, 'Planifiez vos repas\nCuisinez les restes\nDonnez ce que vous ne consommerez pas', '', 'pending', '', NULL, '2026-10-24 20:32:42.789738', '2026-10-24 20:32:42.789799', 2, 10),
(6, 'Consommer local', 'consommer-local', 'Privilégier les produits locaux et de saison pendant un mois.', 'consumption', 'easy', '2026-10-29', '2026-11-28', 30, 60, 3, 'Repérez les marchés de producteurs\nAchetez de saison', '', 'draft', '', NULL, '2026-10-24 20:32:42.801059', '2026-10-24 20:32:42.801101', 5, NULL),
(7, 'Printemps propre', 'printemps-propre', 'Défi terminé de démonstration : opération de collecte de déchets.', 'recycling', 'medium', '2026-07-26', '2026-08-25', 30, 50, 2, 'Rejoignez une collecte\nTriez les déchets ramassés', '', 'completed', '', NULL, '2026-10-24 20:32:42.806909', '2026-10-24 20:32:42.806951', 10, 10),
(8, 'Semaine du covoiturage', 'semaine-du-covoiturage', 'Partagez vos trajets en voiture au moins trois fois sur la période.', 'transport', 'easy', '2026-10-19', '2026-11-18', 30, 55, 3, 'Trouvez un partenaire de trajet\nOrganisez les horaires\nDéclarez chaque trajet partagé', '', 'active', 'Défi de démonstration validé.', '2026-10-19 09:57:00.000000', '2026-10-24 20:32:42.816472', '2026-10-24 20:32:42.821356', 2, 10),
(9, 'Objets qui durent', 'objets-qui-durent', 'Réparez ou donnez une seconde vie à au moins deux objets au lieu de les jeter.', 'consumption', 'medium', '2026-10-24', '2026-11-23', 30, 65, 2, 'Identifiez un objet abîmé\nRéparez-le ou faites-le réparer\nDéclarez chaque réparation', '', 'pending', '', NULL, '2026-10-24 20:32:42.852012', '2026-10-24 20:32:42.852062', 10, 10),
(10, 'Potager partagé', 'potager-partage', 'Défi terminé de démonstration : entretien collectif d’un potager urbain.', 'food', 'hard', '2026-09-14', '2026-10-14', 30, 110, 4, 'Préparez les parcelles\nPlantez et arrosez\nRécoltez et partagez', '', 'completed', '', NULL, '2026-10-24 20:32:42.860828', '2026-10-24 20:32:42.860870', 6, 10);

-- --------------------------------------------------------

--
-- Structure de la table `challenges_challengeparticipation`
--

CREATE TABLE `challenges_challengeparticipation` (
  `id` bigint(20) NOT NULL,
  `status` varchar(20) NOT NULL,
  `joined_at` datetime(6) NOT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `challenge_id` bigint(20) NOT NULL,
  `team_id` bigint(20) DEFAULT NULL,
  `user_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `challenges_challengeparticipation`
--

INSERT INTO `challenges_challengeparticipation` (`id`, `status`, `joined_at`, `completed_at`, `challenge_id`, `team_id`, `user_id`) VALUES
(1, 'completed', '2026-10-05 08:43:00.000000', '2026-10-23 20:12:00.000000', 1, 1, 1),
(2, 'completed', '2026-10-05 08:31:00.000000', '2026-10-23 20:16:00.000000', 1, 1, 2),
(3, 'in_progress', '2026-10-05 08:43:00.000000', NULL, 1, 1, 3),
(4, 'in_progress', '2026-10-05 08:20:00.000000', NULL, 1, 3, 7),
(5, 'completed', '2026-10-09 08:13:00.000000', '2026-10-23 20:58:00.000000', 2, 2, 4),
(6, 'in_progress', '2026-10-09 08:25:00.000000', NULL, 2, 2, 5),
(7, 'in_progress', '2026-10-09 08:16:00.000000', NULL, 2, 1, 2),
(8, 'completed', '2026-10-14 08:22:00.000000', '2026-10-23 20:23:00.000000', 3, 3, 6),
(9, 'in_progress', '2026-10-14 08:59:00.000000', NULL, 3, 3, 7),
(10, 'in_progress', '2026-10-14 08:22:00.000000', NULL, 3, 3, 8),
(11, 'completed', '2026-10-17 08:51:00.000000', '2026-10-23 20:31:00.000000', 4, 4, 9),
(12, 'in_progress', '2026-10-17 08:24:00.000000', NULL, 4, 3, 8),
(13, 'in_progress', '2026-10-17 08:47:00.000000', NULL, 4, 1, 3),
(14, 'in_progress', '2026-10-19 08:32:00.000000', NULL, 8, 1, 2),
(15, 'in_progress', '2026-10-19 08:40:00.000000', NULL, 8, 2, 5),
(16, 'in_progress', '2026-10-24 21:02:38.752668', NULL, 3, 1, 1);

-- --------------------------------------------------------

--
-- Structure de la table `community_event`
--

CREATE TABLE `community_event` (
  `id` bigint(20) NOT NULL,
  `title` varchar(120) NOT NULL,
  `slug` varchar(140) NOT NULL,
  `kind` varchar(10) NOT NULL,
  `description` longtext NOT NULL,
  `category` varchar(20) NOT NULL,
  `format` varchar(10) NOT NULL,
  `location` varchar(160) NOT NULL,
  `online_url` varchar(200) NOT NULL,
  `start_at` datetime(6) NOT NULL,
  `end_at` datetime(6) NOT NULL,
  `target_audience` varchar(20) NOT NULL,
  `capacity` int(10) UNSIGNED DEFAULT NULL CHECK (`capacity` >= 0),
  `participation_goal` int(10) UNSIGNED DEFAULT NULL CHECK (`participation_goal` >= 0),
  `status` varchar(20) NOT NULL,
  `review_notes` longtext NOT NULL,
  `published_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `organizer_id` bigint(20) DEFAULT NULL,
  `reviewed_by_id` bigint(20) DEFAULT NULL
) ;

--
-- Déchargement des données de la table `community_event`
--

INSERT INTO `community_event` (`id`, `title`, `slug`, `kind`, `description`, `category`, `format`, `location`, `online_url`, `start_at`, `end_at`, `target_audience`, `capacity`, `participation_goal`, `status`, `review_notes`, `published_at`, `created_at`, `updated_at`, `organizer_id`, `reviewed_by_id`) VALUES
(1, 'Grand nettoyage de la plage', 'grand-nettoyage-de-la-plage', 'event', 'Ramassage collectif des déchets, tri sur place et pesée des collectes.', 'recycling', 'on_site', 'Plage de La Marsa (lieu fictif de démonstration)', '', '2026-10-29 09:00:00.000000', '2026-10-29 13:00:00.000000', 'all', 40, 30, 'published', 'Publié (démonstration).', '2026-10-24 20:32:51.804688', '2026-10-24 20:32:51.795736', '2026-10-24 20:32:51.804979', 4, 10),
(2, 'Conférence : sobriété énergétique au bureau', 'conference-sobriete-energetique-au-bureau', 'event', 'Bonnes pratiques simples pour réduire la consommation électrique des espaces de travail.', 'energy', 'online', '', 'https://example.org/ecoteams-demo', '2026-10-25 18:00:00.000000', '2026-10-25 20:00:00.000000', 'employees', 100, NULL, 'published', 'Publié (démonstration).', '2026-10-24 20:32:51.844515', '2026-10-24 20:32:51.840816', '2026-10-24 20:32:51.844704', 6, 10),
(3, 'Atelier compost urbain', 'atelier-compost-urbain', 'event', 'Apprendre à composter en appartement et à valoriser ses biodéchets.', 'food', 'hybrid', 'Maison des associations (démo)', 'https://example.org/ecoteams-compost', '2026-11-05 14:00:00.000000', '2026-11-05 17:00:00.000000', 'associations', 25, NULL, 'published', 'Publié (démonstration).', '2026-10-24 20:32:51.871252', '2026-10-24 20:32:51.868003', '2026-10-24 20:32:51.871435', 9, 10),
(4, 'Campagne Mobilité douce', 'campagne-mobilite-douce', 'campaign', 'Un mois pour tester le vélo, la marche et les transports en commun au quotidien.', 'transport', 'online', '', 'https://example.org/ecoteams-mobilite', '2026-10-14 08:00:00.000000', '2026-11-13 08:00:00.000000', 'students', NULL, 30, 'published', 'Publié (démonstration).', '2026-10-24 20:32:51.900765', '2026-10-24 20:32:51.897558', '2026-10-24 20:32:51.900942', 10, 10),
(5, 'Repair café solidaire', 'repair-cafe-solidaire', 'event', 'Réparer ensemble petits appareils, vêtements et vélos.', 'consumption', 'on_site', 'Local associatif (démo)', '', '2026-11-13 15:00:00.000000', '2026-11-13 18:00:00.000000', 'all', 20, NULL, 'pending', '', NULL, '2026-10-24 20:32:51.919267', '2026-10-24 20:32:51.919295', 5, NULL);

-- --------------------------------------------------------

--
-- Structure de la table `community_eventparticipation`
--

CREATE TABLE `community_eventparticipation` (
  `id` bigint(20) NOT NULL,
  `joined_at` datetime(6) NOT NULL,
  `reminder_sent` tinyint(1) NOT NULL,
  `event_id` bigint(20) NOT NULL,
  `team_id` bigint(20) DEFAULT NULL,
  `user_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `community_eventparticipation`
--

INSERT INTO `community_eventparticipation` (`id`, `joined_at`, `reminder_sent`, `event_id`, `team_id`, `user_id`) VALUES
(1, '2026-10-24 20:32:51.935122', 0, 1, 1, 1),
(2, '2026-10-24 20:32:51.979556', 0, 1, 2, 4),
(3, '2026-10-24 20:32:52.019996', 0, 1, 2, 5),
(4, '2026-10-24 20:32:52.039775', 0, 1, 4, 9),
(5, '2026-10-24 20:32:52.086490', 0, 1, 1, 3),
(6, '2026-10-24 20:32:52.123406', 0, 2, 3, 6),
(7, '2026-10-24 20:32:52.163953', 0, 2, 3, 7),
(8, '2026-10-24 20:32:52.209834', 0, 2, 3, 8),
(9, '2026-10-24 20:32:52.251113', 1, 2, 2, 4),
(10, '2026-10-24 20:32:52.291191', 1, 2, 1, 1),
(11, '2026-10-24 20:32:52.336851', 0, 3, 4, 9),
(12, '2026-10-24 20:32:52.385205', 0, 3, 1, 2),
(13, '2026-10-24 20:32:52.439319', 0, 4, 1, 1),
(14, '2026-10-24 20:32:52.467789', 0, 4, 1, 2),
(15, '2026-10-24 20:32:52.521955', 0, 4, 1, 3),
(16, '2026-10-24 20:32:52.626642', 0, 4, 3, 7);

-- --------------------------------------------------------

--
-- Structure de la table `django_admin_log`
--

CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) UNSIGNED NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `django_content_type`
--

CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `django_content_type`
--

INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES
(7, 'accounts', 'role'),
(6, 'accounts', 'user'),
(13, 'actions', 'actionsubmission'),
(12, 'actions', 'ecoactiontype'),
(14, 'actions', 'moderationlog'),
(1, 'admin', 'logentry'),
(23, 'analytics', 'activitylog'),
(3, 'auth', 'group'),
(2, 'auth', 'permission'),
(10, 'challenges', 'challenge'),
(11, 'challenges', 'challengeparticipation'),
(19, 'community', 'event'),
(20, 'community', 'eventparticipation'),
(4, 'contenttypes', 'contenttype'),
(16, 'gamification', 'badge'),
(17, 'gamification', 'pointtransaction'),
(18, 'gamification', 'userbadge'),
(15, 'goals', 'goal'),
(22, 'notifications', 'notification'),
(21, 'notifications', 'notificationpreference'),
(5, 'sessions', 'session'),
(8, 'teams', 'membership'),
(9, 'teams', 'team');

-- --------------------------------------------------------

--
-- Structure de la table `django_migrations`
--

CREATE TABLE `django_migrations` (
  `id` bigint(20) NOT NULL,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `django_migrations`
--

INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES
(1, 'contenttypes', '0001_initial', '2026-10-24 20:32:22.879392'),
(2, 'contenttypes', '0002_remove_content_type_name', '2026-10-24 20:32:22.965933'),
(3, 'auth', '0001_initial', '2026-10-24 20:32:23.295525'),
(4, 'auth', '0002_alter_permission_name_max_length', '2026-10-24 20:32:23.379371'),
(5, 'auth', '0003_alter_user_email_max_length', '2026-10-24 20:32:23.386131'),
(6, 'auth', '0004_alter_user_username_opts', '2026-10-24 20:32:23.393926'),
(7, 'auth', '0005_alter_user_last_login_null', '2026-10-24 20:32:23.400266'),
(8, 'auth', '0006_require_contenttypes_0002', '2026-10-24 20:32:23.403685'),
(9, 'auth', '0007_alter_validators_add_error_messages', '2026-10-24 20:32:23.410125'),
(10, 'auth', '0008_alter_user_username_max_length', '2026-10-24 20:32:23.416783'),
(11, 'auth', '0009_alter_user_last_name_max_length', '2026-10-24 20:32:23.424763'),
(12, 'auth', '0010_alter_group_name_max_length', '2026-10-24 20:32:23.439422'),
(13, 'auth', '0011_update_proxy_permissions', '2026-10-24 20:32:23.448784'),
(14, 'auth', '0012_alter_user_first_name_max_length', '2026-10-24 20:32:23.456599'),
(15, 'accounts', '0001_initial', '2026-10-24 20:32:24.078987'),
(16, 'accounts', '0002_default_role', '2026-10-24 20:32:24.100569'),
(17, 'teams', '0001_initial', '2026-10-24 20:32:24.574255'),
(18, 'challenges', '0001_initial', '2026-10-24 20:32:25.470073'),
(19, 'actions', '0001_initial', '2026-10-24 20:32:26.510436'),
(20, 'actions', '0002_actionsubmission_dedupe_key', '2026-10-24 20:32:26.590204'),
(21, 'admin', '0001_initial', '2026-10-24 20:32:26.800443'),
(22, 'admin', '0002_logentry_remove_auto_add', '2026-10-24 20:32:26.826408'),
(23, 'admin', '0003_logentry_add_action_flag_choices', '2026-10-24 20:32:26.843334'),
(24, 'analytics', '0001_initial', '2026-10-24 20:32:27.132564'),
(25, 'community', '0001_initial', '2026-10-24 20:32:27.837115'),
(26, 'gamification', '0001_initial', '2026-10-24 20:32:28.877528'),
(27, 'goals', '0001_initial', '2026-10-24 20:32:29.022105'),
(28, 'notifications', '0001_initial', '2026-10-24 20:32:29.373402'),
(29, 'sessions', '0001_initial', '2026-10-24 20:32:29.426766'),
(30, 'teams', '0002_membership_captain_of', '2026-10-24 20:32:29.615540');

-- --------------------------------------------------------

--
-- Structure de la table `django_session`
--

CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `django_session`
--

INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES
('3v4qlrd37q4tmrh8nes1eb6twp6q9bg8', '.eJxVjLEKgzAQQP_l5iLJxTTVseBYOnUOd5cTpRrB6FT676Xg0K7vPd4LIu3bEPeiaxwTtGDh9MuY5Kn5K0hk2fNWqgOVqptpnO7ro-iaadbbknS6Hv3fZKAyQAuu98wB1fRqEF3TCHsxtb2oJp8cnyVQooB9jY1RF1KgGtGyIUtsBeH9ARegOhM:1xKhqs:widv7Fgj6ErN3f7P9UZU9rDuDk4aNxKEh7md0esZDvA', '2026-11-07 20:56:26.787189'),
('suk07nflayhofyz379jgg57z7rqh4qe2', '.eJxVjLEKg0AMQP8lcxG95O6MY6Fj6dRZYsyh1Cp4OpX-eyk4tOt7j_eCVvZtaPdsazv20ADD6Zd1og-bv0JUl33ecnGgXFyeMk639Z5tneVp16W36Xz0f5NB8gANOO9djYLESpQil2hCDoNyR7Vn7mKMwkYVpj6FktAra0JxVYjRfID3B90AOLA:1xKxX9:m7mdWOwBCgx7zAE846MncH18MxjzShQbgWOqdPUj7ag', '2026-11-08 13:41:07.473951');

-- --------------------------------------------------------

--
-- Structure de la table `gamification_badge`
--

CREATE TABLE `gamification_badge` (
  `id` bigint(20) NOT NULL,
  `name` varchar(80) NOT NULL,
  `slug` varchar(90) NOT NULL,
  `description` varchar(255) NOT NULL,
  `icon` varchar(30) NOT NULL,
  `tone` varchar(10) NOT NULL,
  `rule` varchar(30) NOT NULL,
  `category` varchar(20) NOT NULL,
  `threshold` int(10) UNSIGNED NOT NULL CHECK (`threshold` >= 0),
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL
) ;

--
-- Déchargement des données de la table `gamification_badge`
--

INSERT INTO `gamification_badge` (`id`, `name`, `slug`, `description`, `icon`, `tone`, `rule`, `category`, `threshold`, `is_active`, `created_at`, `updated_at`) VALUES
(1, 'Premier geste vert', 'premier-geste-vert', 'Valider sa toute première action écologique.', 'sprout', 'lime', 'actions_total', '', 1, 1, '2026-10-24 20:32:33.560636', '2026-10-24 20:32:33.560714'),
(2, 'Éco-débutant', 'eco-debutant', 'Atteindre 50 points au registre.', 'leaf', 'emerald', 'points_total', '', 50, 1, '2026-10-24 20:32:33.568813', '2026-10-24 20:32:33.568889'),
(3, 'Héros du recyclage', 'heros-du-recyclage', 'Valider 5 actions de recyclage.', 'recycle', 'emerald', 'category_actions', 'recycling', 5, 1, '2026-10-24 20:32:33.576480', '2026-10-24 20:32:33.576556'),
(4, 'Cycliste urbain', 'cycliste-urbain', 'Valider 5 actions de mobilité durable.', 'bike', 'cyan', 'category_actions', 'transport', 5, 1, '2026-10-24 20:32:33.583474', '2026-10-24 20:32:33.583504'),
(5, 'Économe en énergie', 'econome-en-energie', 'Valider 5 actions d’économie d’énergie.', 'zap', 'lime', 'category_actions', 'energy', 5, 1, '2026-10-24 20:32:33.588881', '2026-10-24 20:32:33.588943'),
(6, 'Série de 7 jours', 'serie-de-7-jours', 'Valider une action 7 jours consécutifs.', 'flame', 'gold', 'streak_days', '', 7, 1, '2026-10-24 20:32:33.596527', '2026-10-24 20:32:33.596620'),
(7, 'Défi relevé', 'defi-releve', 'Réussir un premier défi écologique.', 'target', 'cyan', 'challenges_completed', '', 1, 1, '2026-10-24 20:32:33.605055', '2026-10-24 20:32:33.605110'),
(8, 'Objectif atteint', 'objectif-atteint', 'Atteindre un objectif personnel.', 'star', 'lime', 'goals_completed', '', 1, 1, '2026-10-24 20:32:33.613289', '2026-10-24 20:32:33.613343'),
(9, 'Citoyen engagé', 'citoyen-engage', 'S’inscrire à 2 événements de la communauté.', 'users', 'cyan', 'events_joined', '', 2, 1, '2026-10-24 20:32:33.619078', '2026-10-24 20:32:33.619134'),
(10, 'Champion d’équipe', 'champion-dequipe', 'Appartenir à l’équipe classée 1re.', 'crown', 'gold', 'team_rank', '', 1, 1, '2026-10-24 20:32:33.624619', '2026-10-24 20:32:33.624671'),
(11, 'Leader de l’action climat', 'leader-de-laction-climat', 'Atteindre 500 points au registre.', 'trophy', 'gold', 'points_total', '', 500, 1, '2026-10-24 20:32:33.631770', '2026-10-24 20:32:33.631827');

-- --------------------------------------------------------

--
-- Structure de la table `gamification_pointtransaction`
--

CREATE TABLE `gamification_pointtransaction` (
  `id` bigint(20) NOT NULL,
  `amount` int(11) NOT NULL,
  `reason` varchar(30) NOT NULL,
  `description` varchar(255) NOT NULL,
  `reference` varchar(120) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `challenge_id` bigint(20) DEFAULT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `submission_id` bigint(20) DEFAULT NULL,
  `team_id` bigint(20) DEFAULT NULL,
  `user_id` bigint(20) NOT NULL
) ;

--
-- Déchargement des données de la table `gamification_pointtransaction`
--

INSERT INTO `gamification_pointtransaction` (`id`, `amount`, `reason`, `description`, `reference`, `created_at`, `challenge_id`, `created_by_id`, `submission_id`, `team_id`, `user_id`) VALUES
(1, 10, 'action_approved', 'Action validée : Transports en commun plutôt que la voiture', 'action:1', '2026-10-13 10:46:00.000000', NULL, NULL, 1, 1, 1),
(2, 10, 'action_approved', 'Action validée : Tri sélectif des déchets', 'action:2', '2026-10-14 10:05:00.000000', NULL, NULL, 2, 2, 4),
(3, 10, 'action_approved', 'Action validée : Transports en commun plutôt que la voiture', 'action:3', '2026-10-15 10:34:00.000000', NULL, NULL, 3, 1, 1),
(4, 10, 'action_approved', 'Action validée : Lutte contre le gaspillage alimentaire', 'action:4', '2026-10-16 10:18:00.000000', NULL, NULL, 4, 1, 2),
(5, 5, 'action_approved', 'Action validée : Gourde et contenants réutilisables', 'action:5', '2026-10-16 10:09:00.000000', NULL, NULL, 5, 2, 5),
(6, 6, 'action_approved', 'Action validée : Lessive à basse température', 'action:6', '2026-10-16 10:41:00.000000', NULL, NULL, 6, 3, 6),
(7, 15, 'action_approved', 'Action validée : Trajet à vélo ou à pied', 'action:7', '2026-10-17 10:45:00.000000', NULL, NULL, 7, 1, 1),
(8, 10, 'action_approved', 'Action validée : Tri sélectif des déchets', 'action:8', '2026-10-17 10:19:00.000000', NULL, NULL, 8, 2, 4),
(9, 12, 'action_approved', 'Action validée : Récupération d’eau de pluie', 'action:9', '2026-10-17 10:54:00.000000', NULL, NULL, 9, 4, 9),
(10, 15, 'action_approved', 'Action validée : Trajet à vélo ou à pied', 'action:10', '2026-10-18 10:23:00.000000', NULL, NULL, 10, 1, 1),
(11, 8, 'action_approved', 'Action validée : Repas végétarien', 'action:11', '2026-10-18 10:29:00.000000', NULL, NULL, 11, 1, 3),
(12, 20, 'action_approved', 'Action validée : Réparer au lieu de jeter', 'action:12', '2026-10-18 10:05:00.000000', NULL, NULL, 12, 2, 4),
(13, 8, 'action_approved', 'Action validée : Éteindre les appareils en veille', 'action:13', '2026-10-18 10:57:00.000000', NULL, NULL, 13, 3, 6),
(14, 15, 'action_approved', 'Action validée : Trajet à vélo ou à pied', 'action:14', '2026-10-19 10:35:00.000000', NULL, NULL, 14, 1, 1),
(15, 15, 'action_approved', 'Action validée : Trajet à vélo ou à pied', 'action:15', '2026-10-19 10:55:00.000000', NULL, NULL, 15, 1, 2),
(16, 10, 'action_approved', 'Action validée : Tri sélectif des déchets', 'action:16', '2026-10-19 10:27:00.000000', NULL, NULL, 16, 2, 4),
(17, 8, 'action_approved', 'Action validée : Éteindre les appareils en veille', 'action:17', '2026-10-19 10:51:00.000000', NULL, NULL, 17, 2, 5),
(18, 8, 'action_approved', 'Action validée : Covoiturage', 'action:18', '2026-10-19 10:55:00.000000', NULL, NULL, 18, 3, 7),
(19, 6, 'action_approved', 'Action validée : Douche de moins de 5 minutes', 'action:19', '2026-10-19 10:56:00.000000', NULL, NULL, 19, 4, 9),
(20, 15, 'action_approved', 'Action validée : Trajet à vélo ou à pied', 'action:20', '2026-10-20 10:25:00.000000', NULL, NULL, 20, 1, 1),
(21, 8, 'action_approved', 'Action validée : Repas végétarien', 'action:21', '2026-10-20 10:33:00.000000', NULL, NULL, 21, 1, 2),
(22, 10, 'action_approved', 'Action validée : Transports en commun plutôt que la voiture', 'action:22', '2026-10-20 10:54:00.000000', NULL, NULL, 22, 1, 3),
(23, 10, 'action_approved', 'Action validée : Tri sélectif des déchets', 'action:23', '2026-10-20 10:36:00.000000', NULL, NULL, 23, 2, 5),
(24, 8, 'action_approved', 'Action validée : Éteindre les appareils en veille', 'action:24', '2026-10-20 10:30:00.000000', NULL, NULL, 24, 3, 6),
(25, 8, 'action_approved', 'Action validée : Éteindre les appareils en veille', 'action:25', '2026-10-20 10:33:00.000000', NULL, NULL, 25, 3, 8),
(26, 6, 'action_approved', 'Action validée : Douche de moins de 5 minutes', 'action:26', '2026-10-20 10:01:00.000000', NULL, NULL, 26, 4, 9),
(27, 15, 'action_approved', 'Action validée : Trajet à vélo ou à pied', 'action:27', '2026-10-21 10:14:00.000000', NULL, NULL, 27, 1, 1),
(28, 15, 'action_approved', 'Action validée : Trajet à vélo ou à pied', 'action:28', '2026-10-21 10:08:00.000000', NULL, NULL, 28, 1, 2),
(29, 6, 'action_approved', 'Action validée : Douche de moins de 5 minutes', 'action:29', '2026-10-21 10:03:00.000000', NULL, NULL, 29, 1, 3),
(30, 10, 'action_approved', 'Action validée : Tri sélectif des déchets', 'action:30', '2026-10-21 10:33:00.000000', NULL, NULL, 30, 2, 4),
(31, 6, 'action_approved', 'Action validée : Lessive à basse température', 'action:31', '2026-10-21 10:42:00.000000', NULL, NULL, 31, 3, 6),
(32, 8, 'action_approved', 'Action validée : Éteindre les appareils en veille', 'action:32', '2026-10-21 10:45:00.000000', NULL, NULL, 32, 3, 7),
(33, 6, 'action_approved', 'Action validée : Douche de moins de 5 minutes', 'action:33', '2026-10-21 10:27:00.000000', NULL, NULL, 33, 4, 9),
(34, 15, 'action_approved', 'Action validée : Trajet à vélo ou à pied', 'action:34', '2026-10-22 10:09:00.000000', NULL, NULL, 34, 1, 1),
(35, 15, 'action_approved', 'Action validée : Trajet à vélo ou à pied', 'action:35', '2026-10-22 10:56:00.000000', NULL, NULL, 35, 1, 2),
(36, 6, 'action_approved', 'Action validée : Douche de moins de 5 minutes', 'action:36', '2026-10-22 10:54:00.000000', NULL, NULL, 36, 1, 3),
(37, 5, 'action_approved', 'Action validée : Gourde et contenants réutilisables', 'action:37', '2026-10-22 10:07:00.000000', NULL, NULL, 37, 2, 4),
(38, 8, 'action_approved', 'Action validée : Éteindre les appareils en veille', 'action:38', '2026-10-22 10:44:00.000000', NULL, NULL, 38, 3, 6),
(39, 6, 'action_approved', 'Action validée : Douche de moins de 5 minutes', 'action:39', '2026-10-22 10:43:00.000000', NULL, NULL, 39, 3, 8),
(40, 6, 'action_approved', 'Action validée : Douche de moins de 5 minutes', 'action:40', '2026-10-22 10:45:00.000000', NULL, NULL, 40, 4, 9),
(41, 15, 'action_approved', 'Action validée : Trajet à vélo ou à pied', 'action:41', '2026-10-23 10:34:00.000000', NULL, NULL, 41, 1, 1),
(42, 10, 'action_approved', 'Action validée : Transports en commun plutôt que la voiture', 'action:42', '2026-10-23 10:35:00.000000', NULL, NULL, 42, 1, 3),
(43, 10, 'action_approved', 'Action validée : Tri sélectif des déchets', 'action:43', '2026-10-23 10:42:00.000000', NULL, NULL, 43, 2, 4),
(44, 10, 'action_approved', 'Action validée : Tri sélectif des déchets', 'action:44', '2026-10-23 10:35:00.000000', NULL, NULL, 44, 2, 5),
(45, 8, 'action_approved', 'Action validée : Éteindre les appareils en veille', 'action:45', '2026-10-23 10:41:00.000000', NULL, NULL, 45, 3, 6),
(46, 8, 'action_approved', 'Action validée : Éteindre les appareils en veille', 'action:46', '2026-10-23 10:44:00.000000', NULL, NULL, 46, 3, 7),
(47, 6, 'action_approved', 'Action validée : Douche de moins de 5 minutes', 'action:47', '2026-10-23 10:51:00.000000', NULL, NULL, 47, 3, 8),
(48, 6, 'action_approved', 'Action validée : Douche de moins de 5 minutes', 'action:48', '2026-10-23 10:25:00.000000', NULL, NULL, 48, 4, 9),
(49, 15, 'action_approved', 'Action validée : Trajet à vélo ou à pied', 'action:49', '2026-10-24 10:12:00.000000', NULL, NULL, 49, 1, 1),
(50, 10, 'action_approved', 'Action validée : Tri sélectif des déchets', 'action:50', '2026-10-24 10:53:00.000000', NULL, NULL, 50, 2, 4),
(51, 8, 'action_approved', 'Action validée : Éteindre les appareils en veille', 'action:51', '2026-10-24 10:00:00.000000', NULL, NULL, 51, 3, 6),
(52, 6, 'action_approved', 'Action validée : Douche de moins de 5 minutes', 'action:52', '2026-10-24 10:09:00.000000', NULL, NULL, 52, 3, 8),
(53, 6, 'action_approved', 'Action validée : Douche de moins de 5 minutes', 'action:53', '2026-10-24 10:56:00.000000', NULL, NULL, 53, 4, 9),
(54, 70, 'challenge_completed', 'Défi réussi : Douches express', 'challenge:4:user:9', '2026-10-23 20:31:00.000000', 4, NULL, NULL, 4, 9),
(55, 90, 'challenge_completed', 'Défi réussi : Chasse au gaspillage énergétique', 'challenge:3:user:6', '2026-10-23 20:23:00.000000', 3, NULL, NULL, 3, 6),
(56, 100, 'challenge_completed', 'Défi réussi : Tri sélectif au quotidien', 'challenge:2:user:4', '2026-10-23 20:58:00.000000', 2, NULL, NULL, 2, 4),
(57, 80, 'challenge_completed', 'Défi réussi : Mois du vélo', 'challenge:1:user:1', '2026-10-23 20:12:00.000000', 1, NULL, NULL, 1, 1),
(58, 80, 'challenge_completed', 'Défi réussi : Mois du vélo', 'challenge:1:user:2', '2026-10-23 20:16:00.000000', 1, NULL, NULL, 1, 2);

-- --------------------------------------------------------

--
-- Structure de la table `gamification_userbadge`
--

CREATE TABLE `gamification_userbadge` (
  `id` bigint(20) NOT NULL,
  `awarded_at` datetime(6) NOT NULL,
  `badge_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `gamification_userbadge`
--

INSERT INTO `gamification_userbadge` (`id`, `awarded_at`, `badge_id`, `user_id`) VALUES
(1, '2026-10-24 20:32:43.270741', 1, 1),
(2, '2026-10-24 20:32:43.282176', 10, 1),
(3, '2026-10-24 20:32:43.360193', 10, 3),
(4, '2026-10-24 20:32:43.399791', 10, 2),
(5, '2026-10-24 20:32:43.544740', 1, 4),
(6, '2026-10-24 20:32:43.557767', 10, 4),
(7, '2026-10-24 20:32:43.613500', 10, 5),
(8, '2026-10-24 20:32:43.858339', 1, 2),
(9, '2026-10-24 20:32:44.088846', 1, 5),
(10, '2026-10-24 20:32:44.220927', 1, 6),
(11, '2026-10-24 20:32:44.624117', 1, 9),
(12, '2026-10-24 20:32:44.737658', 2, 1),
(13, '2026-10-24 20:32:44.884599', 1, 3),
(14, '2026-10-24 20:32:45.302734', 4, 1),
(15, '2026-10-24 20:32:45.673145', 2, 4),
(16, '2026-10-24 20:32:45.924523', 1, 7),
(17, '2026-10-24 20:32:46.854645', 1, 8),
(18, '2026-10-24 20:32:48.077295', 2, 2),
(19, '2026-10-24 20:32:48.436647', 5, 6),
(20, '2026-10-24 20:32:48.989303', 6, 1),
(21, '2026-10-24 20:32:49.285451', 3, 4),
(22, '2026-10-24 20:32:50.343040', 2, 6),
(23, '2026-10-24 20:32:50.806013', 7, 9),
(24, '2026-10-24 20:32:50.816036', 2, 9),
(25, '2026-10-24 20:32:50.975972', 7, 6),
(26, '2026-10-24 20:32:51.060527', 7, 4),
(27, '2026-10-24 20:32:51.167867', 7, 1),
(28, '2026-10-24 20:32:51.291113', 7, 2),
(29, '2026-10-24 20:32:51.957994', 8, 1),
(30, '2026-10-24 20:32:52.001012', 8, 4),
(31, '2026-10-24 20:32:52.271538', 9, 4),
(32, '2026-10-24 20:32:52.310766', 9, 1),
(33, '2026-10-24 20:32:52.365191', 9, 9),
(34, '2026-10-24 20:32:52.417728', 8, 2),
(35, '2026-10-24 20:32:52.496887', 9, 2),
(36, '2026-10-24 20:32:52.571016', 9, 3),
(37, '2026-10-24 20:32:52.674138', 9, 7);

-- --------------------------------------------------------

--
-- Structure de la table `goals_goal`
--

CREATE TABLE `goals_goal` (
  `id` bigint(20) NOT NULL,
  `title` varchar(120) NOT NULL,
  `description` longtext NOT NULL,
  `category` varchar(20) NOT NULL,
  `tracking_mode` varchar(10) NOT NULL,
  `target_value` int(10) UNSIGNED NOT NULL CHECK (`target_value` >= 0),
  `current_progress` int(10) UNSIGNED NOT NULL CHECK (`current_progress` >= 0),
  `unit` varchar(30) NOT NULL,
  `start_date` date NOT NULL,
  `deadline` date NOT NULL,
  `status` varchar(20) NOT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` bigint(20) NOT NULL
) ;

--
-- Déchargement des données de la table `goals_goal`
--

INSERT INTO `goals_goal` (`id`, `title`, `description`, `category`, `tracking_mode`, `target_value`, `current_progress`, `unit`, `start_date`, `deadline`, `status`, `completed_at`, `created_at`, `updated_at`, `user_id`) VALUES
(1, '15 trajets à vélo ce mois-ci', 'Objectif de démonstration.', 'transport', 'actions', 15, 10, 'actions', '2026-10-04', '2026-11-03', 'active', NULL, '2026-10-24 20:32:51.442147', '2026-10-24 20:32:51.457356', 1),
(2, 'Atteindre 200 points', 'Objectif de démonstration.', '', 'points', 200, 220, 'points', '2026-09-29', '2026-11-13', 'completed', '2026-10-24 20:32:51.494821', '2026-10-24 20:32:51.465715', '2026-10-24 20:32:51.495053', 1),
(3, 'Trier chaque semaine', 'Objectif de démonstration.', 'recycling', 'actions', 6, 6, 'actions', '2026-10-04', '2026-11-03', 'completed', '2026-10-24 20:32:51.530752', '2026-10-24 20:32:51.510756', '2026-10-24 20:32:51.530932', 4),
(4, 'Réduire les veilles à zéro', 'Objectif de démonstration.', 'energy', 'actions', 8, 7, 'actions', '2026-10-09', '2026-11-08', 'active', NULL, '2026-10-24 20:32:51.545307', '2026-10-24 20:32:51.557153', 6),
(5, 'Économiser 1 000 litres d’eau', 'Objectif de démonstration.', 'water', 'manual', 1000, 420, 'litres', '2026-10-14', '2026-11-13', 'active', NULL, '2026-10-24 20:32:51.604402', '2026-10-24 20:32:51.604445', 9),
(6, 'Cuisiner 5 repas anti-gaspi', 'Objectif de démonstration.', 'food', 'manual', 5, 2, 'repas', '2026-10-19', '2026-11-18', 'active', NULL, '2026-10-24 20:32:51.614796', '2026-10-24 20:32:51.614840', 2),
(7, 'Prendre les transports en commun 10 fois', 'Objectif de démonstration.', 'transport', 'actions', 10, 2, 'actions', '2026-10-12', '2026-11-11', 'active', NULL, '2026-10-24 20:32:51.622936', '2026-10-24 20:32:51.633319', 3),
(8, 'Trier 5 fois ce mois-ci', 'Objectif de démonstration.', 'recycling', 'actions', 5, 2, 'actions', '2026-10-06', '2026-11-05', 'active', NULL, '2026-10-24 20:32:51.637257', '2026-10-24 20:32:51.647093', 5),
(9, 'Atteindre 150 points', 'Objectif de démonstration.', '', 'points', 150, 24, 'points', '2026-10-04', '2026-11-08', 'active', NULL, '2026-10-24 20:32:51.651315', '2026-10-24 20:32:51.661092', 7),
(10, 'Douches courtes 8 fois', 'Objectif de démonstration.', 'water', 'actions', 8, 3, 'actions', '2026-10-10', '2026-11-07', 'active', NULL, '2026-10-24 20:32:51.665080', '2026-10-24 20:32:51.675482', 8),
(11, 'Covoiturer 3 fois', 'Objectif de démonstration.', 'transport', 'actions', 3, 3, 'actions', '2026-10-16', '2026-11-15', 'completed', '2026-10-24 20:32:51.690559', '2026-10-24 20:32:51.679850', '2026-10-24 20:32:51.690752', 2),
(12, 'Réparer 2 objets au lieu de jeter', 'Objectif de démonstration.', 'consumption', 'manual', 2, 2, 'objets', '2026-10-19', '2026-11-18', 'active', NULL, '2026-10-24 20:32:51.702471', '2026-10-24 20:32:51.702502', 5),
(13, 'Atteindre 300 points', 'Objectif de démonstration.', '', 'points', 300, 142, 'points', '2026-10-02', '2026-11-11', 'active', NULL, '2026-10-24 20:32:51.714621', '2026-10-24 20:32:51.736517', 6),
(14, 'Donner une seconde vie à 2 objets', 'Objectif de démonstration.', 'consumption', 'manual', 2, 2, 'objets', '2026-10-14', '2026-11-13', 'active', NULL, '2026-10-24 20:32:51.741213', '2026-10-24 20:32:51.741254', 10),
(15, 'Prendre les transports en commun 6 fois', 'Objectif de démonstration.', 'transport', 'actions', 6, 0, 'actions', '2026-10-15', '2026-11-09', 'active', NULL, '2026-10-24 20:32:51.749643', '2026-10-24 20:32:51.749681', 9);

-- --------------------------------------------------------

--
-- Structure de la table `notifications_notification`
--

CREATE TABLE `notifications_notification` (
  `id` bigint(20) NOT NULL,
  `kind` varchar(20) NOT NULL,
  `title` varchar(140) NOT NULL,
  `message` longtext NOT NULL,
  `link` varchar(255) NOT NULL,
  `is_read` tinyint(1) NOT NULL,
  `read_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `recipient_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `notifications_notification`
--

INSERT INTO `notifications_notification` (`id`, `kind`, `title`, `message`, `link`, `is_read`, `read_at`, `created_at`, `recipient_id`) VALUES
(1, 'challenge', 'Nouveau défi disponible', '« Mois du vélo » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/mois-du-velo/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:42.659203', 1),
(2, 'challenge', 'Nouveau défi disponible', '« Mois du vélo » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/mois-du-velo/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:42.659293', 2),
(3, 'challenge', 'Nouveau défi disponible', '« Mois du vélo » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/mois-du-velo/', 1, '2026-10-24 20:32:52.704131', '2026-10-24 20:32:42.659389', 3),
(4, 'challenge', 'Nouveau défi disponible', '« Mois du vélo » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/mois-du-velo/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:42.659486', 4),
(5, 'challenge', 'Nouveau défi disponible', '« Mois du vélo » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/mois-du-velo/', 1, '2026-10-24 20:32:52.719808', '2026-10-24 20:32:42.659535', 5),
(6, 'challenge', 'Nouveau défi disponible', '« Mois du vélo » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/mois-du-velo/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:42.659597', 6),
(7, 'challenge', 'Nouveau défi disponible', '« Mois du vélo » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/mois-du-velo/', 1, '2026-10-24 20:32:52.732521', '2026-10-24 20:32:42.659639', 7),
(8, 'challenge', 'Nouveau défi disponible', '« Mois du vélo » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/mois-du-velo/', 1, '2026-10-24 20:32:52.737174', '2026-10-24 20:32:42.659724', 8),
(9, 'challenge', 'Nouveau défi disponible', '« Mois du vélo » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/mois-du-velo/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:42.659769', 9),
(10, 'challenge', 'Votre défi est publié !', '« Tri sélectif au quotidien » a été validé avec 100 points de récompense.', '/challenges/tri-selectif-au-quotidien/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:42.695464', 4),
(11, 'challenge', 'Nouveau défi disponible', '« Tri sélectif au quotidien » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/tri-selectif-au-quotidien/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:42.703112', 1),
(12, 'challenge', 'Nouveau défi disponible', '« Tri sélectif au quotidien » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/tri-selectif-au-quotidien/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:42.703192', 2),
(13, 'challenge', 'Nouveau défi disponible', '« Tri sélectif au quotidien » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/tri-selectif-au-quotidien/', 1, '2026-10-24 20:32:52.704131', '2026-10-24 20:32:42.703227', 3),
(14, 'challenge', 'Nouveau défi disponible', '« Tri sélectif au quotidien » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/tri-selectif-au-quotidien/', 1, '2026-10-24 20:32:52.719808', '2026-10-24 20:32:42.703252', 5),
(15, 'challenge', 'Nouveau défi disponible', '« Tri sélectif au quotidien » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/tri-selectif-au-quotidien/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:42.703280', 6),
(16, 'challenge', 'Nouveau défi disponible', '« Tri sélectif au quotidien » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/tri-selectif-au-quotidien/', 1, '2026-10-24 20:32:52.732521', '2026-10-24 20:32:42.703307', 7),
(17, 'challenge', 'Nouveau défi disponible', '« Tri sélectif au quotidien » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/tri-selectif-au-quotidien/', 1, '2026-10-24 20:32:52.737174', '2026-10-24 20:32:42.703332', 8),
(18, 'challenge', 'Nouveau défi disponible', '« Tri sélectif au quotidien » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/tri-selectif-au-quotidien/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:42.703357', 9),
(19, 'challenge', 'Votre défi est publié !', '« Chasse au gaspillage énergétique » a été validé avec 90 points de récompense.', '/challenges/chasse-au-gaspillage-energetique/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:42.732031', 6),
(20, 'challenge', 'Nouveau défi disponible', '« Chasse au gaspillage énergétique » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/chasse-au-gaspillage-energetique/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:42.741316', 1),
(21, 'challenge', 'Nouveau défi disponible', '« Chasse au gaspillage énergétique » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/chasse-au-gaspillage-energetique/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:42.741387', 2),
(22, 'challenge', 'Nouveau défi disponible', '« Chasse au gaspillage énergétique » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/chasse-au-gaspillage-energetique/', 1, '2026-10-24 20:32:52.704131', '2026-10-24 20:32:42.741432', 3),
(23, 'challenge', 'Nouveau défi disponible', '« Chasse au gaspillage énergétique » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/chasse-au-gaspillage-energetique/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:42.741473', 4),
(24, 'challenge', 'Nouveau défi disponible', '« Chasse au gaspillage énergétique » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/chasse-au-gaspillage-energetique/', 1, '2026-10-24 20:32:52.719808', '2026-10-24 20:32:42.741521', 5),
(25, 'challenge', 'Nouveau défi disponible', '« Chasse au gaspillage énergétique » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/chasse-au-gaspillage-energetique/', 1, '2026-10-24 20:32:52.732521', '2026-10-24 20:32:42.741567', 7),
(26, 'challenge', 'Nouveau défi disponible', '« Chasse au gaspillage énergétique » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/chasse-au-gaspillage-energetique/', 1, '2026-10-24 20:32:52.737174', '2026-10-24 20:32:42.741619', 8),
(27, 'challenge', 'Nouveau défi disponible', '« Chasse au gaspillage énergétique » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/chasse-au-gaspillage-energetique/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:42.741662', 9),
(28, 'challenge', 'Votre défi est publié !', '« Douches express » a été validé avec 70 points de récompense.', '/challenges/douches-express/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:42.769972', 9),
(29, 'challenge', 'Nouveau défi disponible', '« Douches express » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/douches-express/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:42.777158', 1),
(30, 'challenge', 'Nouveau défi disponible', '« Douches express » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/douches-express/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:42.777226', 2),
(31, 'challenge', 'Nouveau défi disponible', '« Douches express » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/douches-express/', 1, '2026-10-24 20:32:52.704131', '2026-10-24 20:32:42.777274', 3),
(32, 'challenge', 'Nouveau défi disponible', '« Douches express » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/douches-express/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:42.777319', 4),
(33, 'challenge', 'Nouveau défi disponible', '« Douches express » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/douches-express/', 1, '2026-10-24 20:32:52.719808', '2026-10-24 20:32:42.777362', 5),
(34, 'challenge', 'Nouveau défi disponible', '« Douches express » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/douches-express/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:42.777408', 6),
(35, 'challenge', 'Nouveau défi disponible', '« Douches express » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/douches-express/', 1, '2026-10-24 20:32:52.732521', '2026-10-24 20:32:42.777452', 7),
(36, 'challenge', 'Nouveau défi disponible', '« Douches express » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/douches-express/', 1, '2026-10-24 20:32:52.737174', '2026-10-24 20:32:42.777493', 8),
(37, 'challenge', 'Votre défi est publié !', '« Semaine du covoiturage » a été validé avec 55 points de récompense.', '/challenges/semaine-du-covoiturage/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:42.831036', 2),
(38, 'challenge', 'Nouveau défi disponible', '« Semaine du covoiturage » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/semaine-du-covoiturage/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:42.839340', 1),
(39, 'challenge', 'Nouveau défi disponible', '« Semaine du covoiturage » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/semaine-du-covoiturage/', 1, '2026-10-24 20:32:52.704131', '2026-10-24 20:32:42.839428', 3),
(40, 'challenge', 'Nouveau défi disponible', '« Semaine du covoiturage » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/semaine-du-covoiturage/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:42.839476', 4),
(41, 'challenge', 'Nouveau défi disponible', '« Semaine du covoiturage » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/semaine-du-covoiturage/', 1, '2026-10-24 20:32:52.719808', '2026-10-24 20:32:42.839562', 5),
(42, 'challenge', 'Nouveau défi disponible', '« Semaine du covoiturage » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/semaine-du-covoiturage/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:42.839609', 6),
(43, 'challenge', 'Nouveau défi disponible', '« Semaine du covoiturage » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/semaine-du-covoiturage/', 1, '2026-10-24 20:32:52.732521', '2026-10-24 20:32:42.839675', 7),
(44, 'challenge', 'Nouveau défi disponible', '« Semaine du covoiturage » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/semaine-du-covoiturage/', 1, '2026-10-24 20:32:52.737174', '2026-10-24 20:32:42.839720', 8),
(45, 'challenge', 'Nouveau défi disponible', '« Semaine du covoiturage » vient d’être lancé. Relevez-le avec votre équipe !', '/challenges/semaine-du-covoiturage/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:42.839760', 9),
(46, 'action', 'Action validée', 'Votre action « Transports en commun plutôt que la voiture » a été validée par la modération.', '/actions/1/', 1, '2026-10-24 20:32:52.688923', '2026-10-13 10:46:00.000000', 1),
(47, 'points', '+10 points', 'Action validée : Transports en commun plutôt que la voiture', '/history/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:43.230519', 1),
(48, 'badge', 'Badge débloqué : Premier geste vert', 'Valider sa toute première action écologique.', '/achievements/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:43.275008', 1),
(49, 'badge', 'Badge débloqué : Champion d’équipe', 'Appartenir à l’équipe classée 1re.', '/achievements/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:43.293954', 1),
(50, 'badge', 'Badge débloqué : Champion d’équipe', 'Appartenir à l’équipe classée 1re.', '/achievements/', 1, '2026-10-24 20:32:52.704131', '2026-10-24 20:32:43.363863', 3),
(51, 'badge', 'Badge débloqué : Champion d’équipe', 'Appartenir à l’équipe classée 1re.', '/achievements/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:43.403021', 2),
(52, 'action', 'Action validée', 'Votre action « Tri sélectif des déchets » a été validée par la modération.', '/actions/2/', 1, '2026-10-24 20:32:52.710930', '2026-10-14 10:05:00.000000', 4),
(53, 'points', '+10 points', 'Action validée : Tri sélectif des déchets', '/history/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:43.507251', 4),
(54, 'badge', 'Badge débloqué : Premier geste vert', 'Valider sa toute première action écologique.', '/achievements/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:43.549260', 4),
(55, 'badge', 'Badge débloqué : Champion d’équipe', 'Appartenir à l’équipe classée 1re.', '/achievements/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:43.562042', 4),
(56, 'badge', 'Badge débloqué : Champion d’équipe', 'Appartenir à l’équipe classée 1re.', '/achievements/', 1, '2026-10-24 20:32:52.719808', '2026-10-24 20:32:43.618950', 5),
(57, 'action', 'Action validée', 'Votre action « Transports en commun plutôt que la voiture » a été validée par la modération.', '/actions/3/', 1, '2026-10-24 20:32:52.688923', '2026-10-15 10:34:00.000000', 1),
(58, 'points', '+10 points', 'Action validée : Transports en commun plutôt que la voiture', '/history/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:43.689172', 1),
(59, 'action', 'Action validée', 'Votre action « Lutte contre le gaspillage alimentaire » a été validée par la modération.', '/actions/4/', 1, '2026-10-24 20:32:52.697095', '2026-10-16 10:18:00.000000', 2),
(60, 'points', '+10 points', 'Action validée : Lutte contre le gaspillage alimentaire', '/history/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:43.824764', 2),
(61, 'badge', 'Badge débloqué : Premier geste vert', 'Valider sa toute première action écologique.', '/achievements/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:43.862918', 2),
(62, 'action', 'Action validée', 'Votre action « Gourde et contenants réutilisables » a été validée par la modération.', '/actions/5/', 1, '2026-10-24 20:32:52.719808', '2026-10-16 10:09:00.000000', 5),
(63, 'points', '+5 points', 'Action validée : Gourde et contenants réutilisables', '/history/', 1, '2026-10-24 20:32:52.719808', '2026-10-24 20:32:44.057653', 5),
(64, 'badge', 'Badge débloqué : Premier geste vert', 'Valider sa toute première action écologique.', '/achievements/', 1, '2026-10-24 20:32:52.719808', '2026-10-24 20:32:44.093067', 5),
(65, 'action', 'Action validée', 'Votre action « Lessive à basse température » a été validée par la modération.', '/actions/6/', 1, '2026-10-24 20:32:52.724455', '2026-10-16 10:41:00.000000', 6),
(66, 'points', '+6 points', 'Action validée : Lessive à basse température', '/history/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:44.186928', 6),
(67, 'badge', 'Badge débloqué : Premier geste vert', 'Valider sa toute première action écologique.', '/achievements/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:44.225807', 6),
(68, 'action', 'Action validée', 'Votre action « Trajet à vélo ou à pied » a été validée par la modération.', '/actions/7/', 1, '2026-10-24 20:32:52.688923', '2026-10-17 10:45:00.000000', 1),
(69, 'points', '+15 points', 'Action validée : Trajet à vélo ou à pied', '/history/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:44.303556', 1),
(70, 'action', 'Action validée', 'Votre action « Tri sélectif des déchets » a été validée par la modération.', '/actions/8/', 1, '2026-10-24 20:32:52.710930', '2026-10-17 10:19:00.000000', 4),
(71, 'points', '+10 points', 'Action validée : Tri sélectif des déchets', '/history/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:44.458410', 4),
(72, 'action', 'Action validée', 'Votre action « Récupération d’eau de pluie » a été validée par la modération.', '/actions/9/', 1, '2026-10-24 20:32:52.741914', '2026-10-17 10:54:00.000000', 9),
(73, 'points', '+12 points', 'Action validée : Récupération d’eau de pluie', '/history/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:44.589535', 9),
(74, 'badge', 'Badge débloqué : Premier geste vert', 'Valider sa toute première action écologique.', '/achievements/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:44.628215', 9),
(75, 'action', 'Action validée', 'Votre action « Trajet à vélo ou à pied » a été validée par la modération.', '/actions/10/', 1, '2026-10-24 20:32:52.688923', '2026-10-18 10:23:00.000000', 1),
(76, 'points', '+15 points', 'Action validée : Trajet à vélo ou à pied', '/history/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:44.710702', 1),
(77, 'badge', 'Badge débloqué : Éco-débutant', 'Atteindre 50 points au registre.', '/achievements/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:44.741050', 1),
(78, 'action', 'Action validée', 'Votre action « Repas végétarien » a été validée par la modération.', '/actions/11/', 1, '2026-10-24 20:32:52.704131', '2026-10-18 10:29:00.000000', 3),
(79, 'points', '+8 points', 'Action validée : Repas végétarien', '/history/', 1, '2026-10-24 20:32:52.704131', '2026-10-24 20:32:44.852588', 3),
(80, 'badge', 'Badge débloqué : Premier geste vert', 'Valider sa toute première action écologique.', '/achievements/', 1, '2026-10-24 20:32:52.704131', '2026-10-24 20:32:44.888434', 3),
(81, 'action', 'Action validée', 'Votre action « Réparer au lieu de jeter » a été validée par la modération.', '/actions/12/', 1, '2026-10-24 20:32:52.710930', '2026-10-18 10:05:00.000000', 4),
(82, 'points', '+20 points', 'Action validée : Réparer au lieu de jeter', '/history/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:45.008892', 4),
(83, 'action', 'Action validée', 'Votre action « Éteindre les appareils en veille » a été validée par la modération.', '/actions/13/', 1, '2026-10-24 20:32:52.724455', '2026-10-18 10:57:00.000000', 6),
(84, 'points', '+8 points', 'Action validée : Éteindre les appareils en veille', '/history/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:45.164435', 6),
(85, 'action', 'Action validée', 'Votre action « Trajet à vélo ou à pied » a été validée par la modération.', '/actions/14/', 1, '2026-10-24 20:32:52.688923', '2026-10-19 10:35:00.000000', 1),
(86, 'points', '+15 points', 'Action validée : Trajet à vélo ou à pied', '/history/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:45.280655', 1),
(87, 'badge', 'Badge débloqué : Cycliste urbain', 'Valider 5 actions de mobilité durable.', '/achievements/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:45.305868', 1),
(88, 'challenge', 'Défi prêt à être validé', 'Vous avez rempli les conditions du défi « Mois du vélo ». Validez votre réussite !', '/challenges/mois-du-velo/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:45.428338', 1),
(89, 'action', 'Action validée', 'Votre action « Trajet à vélo ou à pied » a été validée par la modération.', '/actions/15/', 1, '2026-10-24 20:32:52.697095', '2026-10-19 10:55:00.000000', 2),
(90, 'points', '+15 points', 'Action validée : Trajet à vélo ou à pied', '/history/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:45.488494', 2),
(91, 'action', 'Action validée', 'Votre action « Tri sélectif des déchets » a été validée par la modération.', '/actions/16/', 1, '2026-10-24 20:32:52.710930', '2026-10-19 10:27:00.000000', 4),
(92, 'points', '+10 points', 'Action validée : Tri sélectif des déchets', '/history/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:45.644724', 4),
(93, 'badge', 'Badge débloqué : Éco-débutant', 'Atteindre 50 points au registre.', '/achievements/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:45.676415', 4),
(94, 'action', 'Action validée', 'Votre action « Éteindre les appareils en veille » a été validée par la modération.', '/actions/17/', 1, '2026-10-24 20:32:52.719808', '2026-10-19 10:51:00.000000', 5),
(95, 'points', '+8 points', 'Action validée : Éteindre les appareils en veille', '/history/', 1, '2026-10-24 20:32:52.719808', '2026-10-24 20:32:45.802622', 5),
(96, 'action', 'Action validée', 'Votre action « Covoiturage » a été validée par la modération.', '/actions/18/', 1, '2026-10-24 20:32:52.732521', '2026-10-19 10:55:00.000000', 7),
(97, 'points', '+8 points', 'Action validée : Covoiturage', '/history/', 1, '2026-10-24 20:32:52.732521', '2026-10-24 20:32:45.888721', 7),
(98, 'badge', 'Badge débloqué : Premier geste vert', 'Valider sa toute première action écologique.', '/achievements/', 1, '2026-10-24 20:32:52.732521', '2026-10-24 20:32:45.928801', 7),
(99, 'action', 'Action validée', 'Votre action « Douche de moins de 5 minutes » a été validée par la modération.', '/actions/19/', 1, '2026-10-24 20:32:52.741914', '2026-10-19 10:56:00.000000', 9),
(100, 'points', '+6 points', 'Action validée : Douche de moins de 5 minutes', '/history/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:46.005041', 9),
(101, 'action', 'Action validée', 'Votre action « Trajet à vélo ou à pied » a été validée par la modération.', '/actions/20/', 1, '2026-10-24 20:32:52.688923', '2026-10-20 10:25:00.000000', 1),
(102, 'points', '+15 points', 'Action validée : Trajet à vélo ou à pied', '/history/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:46.131702', 1),
(103, 'leaderboard', 'Cap des 100 points franchi !', 'L’équipe « Les Pédaleurs Verts » totalise désormais 113 points. Bravo à toute l’équipe !', '/leaderboard/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:46.217491', 1),
(104, 'leaderboard', 'Cap des 100 points franchi !', 'L’équipe « Les Pédaleurs Verts » totalise désormais 113 points. Bravo à toute l’équipe !', '/leaderboard/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:46.217578', 2),
(105, 'leaderboard', 'Cap des 100 points franchi !', 'L’équipe « Les Pédaleurs Verts » totalise désormais 113 points. Bravo à toute l’équipe !', '/leaderboard/', 1, '2026-10-24 20:32:52.704131', '2026-10-24 20:32:46.217627', 3),
(106, 'action', 'Action validée', 'Votre action « Repas végétarien » a été validée par la modération.', '/actions/21/', 1, '2026-10-24 20:32:52.697095', '2026-10-20 10:33:00.000000', 2),
(107, 'points', '+8 points', 'Action validée : Repas végétarien', '/history/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:46.328075', 2),
(108, 'action', 'Action validée', 'Votre action « Transports en commun plutôt que la voiture » a été validée par la modération.', '/actions/22/', 1, '2026-10-24 20:32:52.704131', '2026-10-20 10:54:00.000000', 3),
(109, 'points', '+10 points', 'Action validée : Transports en commun plutôt que la voiture', '/history/', 1, '2026-10-24 20:32:52.704131', '2026-10-24 20:32:46.488169', 3),
(110, 'action', 'Action validée', 'Votre action « Tri sélectif des déchets » a été validée par la modération.', '/actions/23/', 1, '2026-10-24 20:32:52.719808', '2026-10-20 10:36:00.000000', 5),
(111, 'points', '+10 points', 'Action validée : Tri sélectif des déchets', '/history/', 1, '2026-10-24 20:32:52.719808', '2026-10-24 20:32:46.612577', 5),
(112, 'action', 'Action validée', 'Votre action « Éteindre les appareils en veille » a été validée par la modération.', '/actions/24/', 1, '2026-10-24 20:32:52.724455', '2026-10-20 10:30:00.000000', 6),
(113, 'points', '+8 points', 'Action validée : Éteindre les appareils en veille', '/history/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:46.707542', 6),
(114, 'action', 'Action validée', 'Votre action « Éteindre les appareils en veille » a été validée par la modération.', '/actions/25/', 1, '2026-10-24 20:32:52.737174', '2026-10-20 10:33:00.000000', 8),
(115, 'points', '+8 points', 'Action validée : Éteindre les appareils en veille', '/history/', 1, '2026-10-24 20:32:52.737174', '2026-10-24 20:32:46.816504', 8),
(116, 'badge', 'Badge débloqué : Premier geste vert', 'Valider sa toute première action écologique.', '/achievements/', 1, '2026-10-24 20:32:52.737174', '2026-10-24 20:32:46.858134', 8),
(117, 'action', 'Action validée', 'Votre action « Douche de moins de 5 minutes » a été validée par la modération.', '/actions/26/', 1, '2026-10-24 20:32:52.741914', '2026-10-20 10:01:00.000000', 9),
(118, 'points', '+6 points', 'Action validée : Douche de moins de 5 minutes', '/history/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:46.929068', 9),
(119, 'action', 'Action validée', 'Votre action « Trajet à vélo ou à pied » a été validée par la modération.', '/actions/27/', 1, '2026-10-24 20:32:52.688923', '2026-10-21 10:14:00.000000', 1),
(120, 'points', '+15 points', 'Action validée : Trajet à vélo ou à pied', '/history/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:47.043500', 1),
(121, 'action', 'Action validée', 'Votre action « Trajet à vélo ou à pied » a été validée par la modération.', '/actions/28/', 1, '2026-10-24 20:32:52.697095', '2026-10-21 10:08:00.000000', 2),
(122, 'points', '+15 points', 'Action validée : Trajet à vélo ou à pied', '/history/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:47.210565', 2),
(123, 'action', 'Action validée', 'Votre action « Douche de moins de 5 minutes » a été validée par la modération.', '/actions/29/', 1, '2026-10-24 20:32:52.704131', '2026-10-21 10:03:00.000000', 3),
(124, 'points', '+6 points', 'Action validée : Douche de moins de 5 minutes', '/history/', 1, '2026-10-24 20:32:52.704131', '2026-10-24 20:32:47.366418', 3),
(125, 'action', 'Action validée', 'Votre action « Tri sélectif des déchets » a été validée par la modération.', '/actions/30/', 1, '2026-10-24 20:32:52.710930', '2026-10-21 10:33:00.000000', 4),
(126, 'points', '+10 points', 'Action validée : Tri sélectif des déchets', '/history/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:47.549669', 4),
(127, 'challenge', 'Défi prêt à être validé', 'Vous avez rempli les conditions du défi « Tri sélectif au quotidien ». Validez votre réussite !', '/challenges/tri-selectif-au-quotidien/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:47.609734', 4),
(128, 'action', 'Action validée', 'Votre action « Lessive à basse température » a été validée par la modération.', '/actions/31/', 1, '2026-10-24 20:32:52.724455', '2026-10-21 10:42:00.000000', 6),
(129, 'points', '+6 points', 'Action validée : Lessive à basse température', '/history/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:47.668260', 6),
(130, 'action', 'Action validée', 'Votre action « Éteindre les appareils en veille » a été validée par la modération.', '/actions/32/', 1, '2026-10-24 20:32:52.732521', '2026-10-21 10:45:00.000000', 7),
(131, 'points', '+8 points', 'Action validée : Éteindre les appareils en veille', '/history/', 1, '2026-10-24 20:32:52.732521', '2026-10-24 20:32:47.777884', 7),
(132, 'action', 'Action validée', 'Votre action « Douche de moins de 5 minutes » a été validée par la modération.', '/actions/33/', 1, '2026-10-24 20:32:52.741914', '2026-10-21 10:27:00.000000', 9),
(133, 'points', '+6 points', 'Action validée : Douche de moins de 5 minutes', '/history/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:47.886592', 9),
(134, 'action', 'Action validée', 'Votre action « Trajet à vélo ou à pied » a été validée par la modération.', '/actions/34/', 1, '2026-10-24 20:32:52.688923', '2026-10-22 10:09:00.000000', 1),
(135, 'points', '+15 points', 'Action validée : Trajet à vélo ou à pied', '/history/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:47.981067', 1),
(136, 'action', 'Action validée', 'Votre action « Trajet à vélo ou à pied » a été validée par la modération.', '/actions/35/', 1, '2026-10-24 20:32:52.697095', '2026-10-22 10:56:00.000000', 2),
(137, 'points', '+15 points', 'Action validée : Trajet à vélo ou à pied', '/history/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:48.067720', 2),
(138, 'badge', 'Badge débloqué : Éco-débutant', 'Atteindre 50 points au registre.', '/achievements/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:48.078628', 2),
(139, 'challenge', 'Défi prêt à être validé', 'Vous avez rempli les conditions du défi « Mois du vélo ». Validez votre réussite !', '/challenges/mois-du-velo/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:48.155338', 2),
(140, 'action', 'Action validée', 'Votre action « Douche de moins de 5 minutes » a été validée par la modération.', '/actions/36/', 1, '2026-10-24 20:32:52.704131', '2026-10-22 10:54:00.000000', 3),
(141, 'points', '+6 points', 'Action validée : Douche de moins de 5 minutes', '/history/', 1, '2026-10-24 20:32:52.704131', '2026-10-24 20:32:48.196134', 3),
(142, 'action', 'Action validée', 'Votre action « Gourde et contenants réutilisables » a été validée par la modération.', '/actions/37/', 1, '2026-10-24 20:32:52.710930', '2026-10-22 10:07:00.000000', 4),
(143, 'points', '+5 points', 'Action validée : Gourde et contenants réutilisables', '/history/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:48.302054', 4),
(144, 'action', 'Action validée', 'Votre action « Éteindre les appareils en veille » a été validée par la modération.', '/actions/38/', 1, '2026-10-24 20:32:52.724455', '2026-10-22 10:44:00.000000', 6),
(145, 'points', '+8 points', 'Action validée : Éteindre les appareils en veille', '/history/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:48.406310', 6),
(146, 'badge', 'Badge débloqué : Économe en énergie', 'Valider 5 actions d’économie d’énergie.', '/achievements/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:48.439621', 6),
(147, 'challenge', 'Défi prêt à être validé', 'Vous avez rempli les conditions du défi « Chasse au gaspillage énergétique ». Validez votre réussite !', '/challenges/chasse-au-gaspillage-energetique/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:48.476479', 6),
(148, 'action', 'Action validée', 'Votre action « Douche de moins de 5 minutes » a été validée par la modération.', '/actions/39/', 1, '2026-10-24 20:32:52.737174', '2026-10-22 10:43:00.000000', 8),
(149, 'points', '+6 points', 'Action validée : Douche de moins de 5 minutes', '/history/', 1, '2026-10-24 20:32:52.737174', '2026-10-24 20:32:48.558768', 8),
(150, 'action', 'Action validée', 'Votre action « Douche de moins de 5 minutes » a été validée par la modération.', '/actions/40/', 1, '2026-10-24 20:32:52.741914', '2026-10-22 10:45:00.000000', 9),
(151, 'points', '+6 points', 'Action validée : Douche de moins de 5 minutes', '/history/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:48.679404', 9),
(152, 'action', 'Action validée', 'Votre action « Trajet à vélo ou à pied » a été validée par la modération.', '/actions/41/', 1, '2026-10-24 20:32:52.688923', '2026-10-23 10:34:00.000000', 1),
(153, 'points', '+15 points', 'Action validée : Trajet à vélo ou à pied', '/history/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:48.944237', 1),
(154, 'badge', 'Badge débloqué : Série de 7 jours', 'Valider une action 7 jours consécutifs.', '/achievements/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:48.994472', 1),
(155, 'action', 'Action validée', 'Votre action « Transports en commun plutôt que la voiture » a été validée par la modération.', '/actions/42/', 1, '2026-10-24 20:32:52.704131', '2026-10-23 10:35:00.000000', 3),
(156, 'points', '+10 points', 'Action validée : Transports en commun plutôt que la voiture', '/history/', 1, '2026-10-24 20:32:52.704131', '2026-10-24 20:32:49.135539', 3),
(157, 'action', 'Action validée', 'Votre action « Tri sélectif des déchets » a été validée par la modération.', '/actions/43/', 1, '2026-10-24 20:32:52.710930', '2026-10-23 10:42:00.000000', 4),
(158, 'points', '+10 points', 'Action validée : Tri sélectif des déchets', '/history/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:49.262285', 4),
(159, 'badge', 'Badge débloqué : Héros du recyclage', 'Valider 5 actions de recyclage.', '/achievements/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:49.288564', 4),
(160, 'action', 'Action validée', 'Votre action « Tri sélectif des déchets » a été validée par la modération.', '/actions/44/', 1, '2026-10-24 20:32:52.719808', '2026-10-23 10:35:00.000000', 5),
(161, 'points', '+10 points', 'Action validée : Tri sélectif des déchets', '/history/', 1, '2026-10-24 20:32:52.719808', '2026-10-24 20:32:49.362228', 5),
(162, 'leaderboard', 'Cap des 100 points franchi !', 'L’équipe « Zéro Déchet Squad » totalise désormais 108 points. Bravo à toute l’équipe !', '/leaderboard/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:49.398213', 4),
(163, 'leaderboard', 'Cap des 100 points franchi !', 'L’équipe « Zéro Déchet Squad » totalise désormais 108 points. Bravo à toute l’équipe !', '/leaderboard/', 0, NULL, '2026-10-24 20:32:49.398289', 5),
(164, 'action', 'Action validée', 'Votre action « Éteindre les appareils en veille » a été validée par la modération.', '/actions/45/', 1, '2026-10-24 20:32:52.724455', '2026-10-23 10:41:00.000000', 6),
(165, 'points', '+8 points', 'Action validée : Éteindre les appareils en veille', '/history/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:49.475207', 6),
(166, 'action', 'Action validée', 'Votre action « Éteindre les appareils en veille » a été validée par la modération.', '/actions/46/', 1, '2026-10-24 20:32:52.732521', '2026-10-23 10:44:00.000000', 7),
(167, 'points', '+8 points', 'Action validée : Éteindre les appareils en veille', '/history/', 1, '2026-10-24 20:32:52.732521', '2026-10-24 20:32:49.617227', 7),
(168, 'action', 'Action validée', 'Votre action « Douche de moins de 5 minutes » a été validée par la modération.', '/actions/47/', 1, '2026-10-24 20:32:52.737174', '2026-10-23 10:51:00.000000', 8),
(169, 'points', '+6 points', 'Action validée : Douche de moins de 5 minutes', '/history/', 1, '2026-10-24 20:32:52.737174', '2026-10-24 20:32:49.716809', 8),
(170, 'action', 'Action validée', 'Votre action « Douche de moins de 5 minutes » a été validée par la modération.', '/actions/48/', 1, '2026-10-24 20:32:52.741914', '2026-10-23 10:25:00.000000', 9),
(171, 'points', '+6 points', 'Action validée : Douche de moins de 5 minutes', '/history/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:49.860739', 9),
(172, 'challenge', 'Défi prêt à être validé', 'Vous avez rempli les conditions du défi « Douches express ». Validez votre réussite !', '/challenges/douches-express/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:49.949913', 9),
(173, 'action', 'Action validée', 'Votre action « Trajet à vélo ou à pied » a été validée par la modération.', '/actions/49/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 10:12:00.000000', 1),
(174, 'points', '+15 points', 'Action validée : Trajet à vélo ou à pied', '/history/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:50.001286', 1),
(175, 'action', 'Action validée', 'Votre action « Tri sélectif des déchets » a été validée par la modération.', '/actions/50/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 10:53:00.000000', 4),
(176, 'points', '+10 points', 'Action validée : Tri sélectif des déchets', '/history/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:50.159385', 4),
(177, 'action', 'Action validée', 'Votre action « Éteindre les appareils en veille » a été validée par la modération.', '/actions/51/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 10:00:00.000000', 6),
(178, 'points', '+8 points', 'Action validée : Éteindre les appareils en veille', '/history/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:50.311939', 6),
(179, 'badge', 'Badge débloqué : Éco-débutant', 'Atteindre 50 points au registre.', '/achievements/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:50.346500', 6),
(180, 'action', 'Action validée', 'Votre action « Douche de moins de 5 minutes » a été validée par la modération.', '/actions/52/', 1, '2026-10-24 20:32:52.737174', '2026-10-24 10:09:00.000000', 8),
(181, 'points', '+6 points', 'Action validée : Douche de moins de 5 minutes', '/history/', 1, '2026-10-24 20:32:52.737174', '2026-10-24 20:32:50.430366', 8),
(182, 'leaderboard', 'Cap des 100 points franchi !', 'L’équipe « Watt Watchers » totalise désormais 102 points. Bravo à toute l’équipe !', '/leaderboard/', 0, NULL, '2026-10-24 20:32:50.474590', 8),
(183, 'leaderboard', 'Cap des 100 points franchi !', 'L’équipe « Watt Watchers » totalise désormais 102 points. Bravo à toute l’équipe !', '/leaderboard/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:50.474663', 6),
(184, 'leaderboard', 'Cap des 100 points franchi !', 'L’équipe « Watt Watchers » totalise désormais 102 points. Bravo à toute l’équipe !', '/leaderboard/', 1, '2026-10-24 20:32:52.732521', '2026-10-24 20:32:50.474714', 7),
(185, 'action', 'Action validée', 'Votre action « Douche de moins de 5 minutes » a été validée par la modération.', '/actions/53/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 10:56:00.000000', 9),
(186, 'points', '+6 points', 'Action validée : Douche de moins de 5 minutes', '/history/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:50.541668', 9),
(187, 'action', 'Action refusée', '« Réparer au lieu de jeter » a été refusée : La photo justificative est obligatoire pour cette action.', '/actions/58/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:50.703166', 2),
(188, 'challenge', 'Défi réussi !', 'Bravo, vous avez réussi « Douches express ».', '/challenges/douches-express/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:50.769186', 9),
(189, 'points', '+70 points', 'Défi réussi : Douches express', '/history/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:50.778101', 9),
(190, 'badge', 'Badge débloqué : Défi relevé', 'Réussir un premier défi écologique.', '/achievements/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:50.809090', 9),
(191, 'badge', 'Badge débloqué : Éco-débutant', 'Atteindre 50 points au registre.', '/achievements/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:50.819010', 9),
(192, 'leaderboard', 'Cap des 100 points franchi !', 'L’équipe « Gouttes d’Avenir » totalise désormais 118 points. Bravo à toute l’équipe !', '/leaderboard/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:50.877699', 9),
(193, 'challenge', 'Défi réussi !', 'Bravo, vous avez réussi « Chasse au gaspillage énergétique ».', '/challenges/chasse-au-gaspillage-energetique/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:50.936151', 6),
(194, 'points', '+90 points', 'Défi réussi : Chasse au gaspillage énergétique', '/history/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:50.946396', 6),
(195, 'badge', 'Badge débloqué : Défi relevé', 'Réussir un premier défi écologique.', '/achievements/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:50.980309', 6),
(196, 'challenge', 'Défi réussi !', 'Bravo, vous avez réussi « Tri sélectif au quotidien ».', '/challenges/tri-selectif-au-quotidien/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:51.031463', 4),
(197, 'points', '+100 points', 'Défi réussi : Tri sélectif au quotidien', '/history/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:51.038066', 4),
(198, 'badge', 'Badge débloqué : Défi relevé', 'Réussir un premier défi écologique.', '/achievements/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:51.063658', 4),
(199, 'challenge', 'Défi réussi !', 'Bravo, vous avez réussi « Mois du vélo ».', '/challenges/mois-du-velo/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:51.134225', 1),
(200, 'points', '+80 points', 'Défi réussi : Mois du vélo', '/history/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:51.143968', 1),
(201, 'badge', 'Badge débloqué : Défi relevé', 'Réussir un premier défi écologique.', '/achievements/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:51.171474', 1),
(202, 'leaderboard', 'Cap des 250 points franchi !', 'L’équipe « Les Pédaleurs Verts » totalise désormais 323 points. Bravo à toute l’équipe !', '/leaderboard/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:51.190797', 1),
(203, 'leaderboard', 'Cap des 250 points franchi !', 'L’équipe « Les Pédaleurs Verts » totalise désormais 323 points. Bravo à toute l’équipe !', '/leaderboard/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:51.190844', 2),
(204, 'leaderboard', 'Cap des 250 points franchi !', 'L’équipe « Les Pédaleurs Verts » totalise désormais 323 points. Bravo à toute l’équipe !', '/leaderboard/', 1, '2026-10-24 20:32:52.704131', '2026-10-24 20:32:51.190872', 3),
(205, 'challenge', 'Défi réussi !', 'Bravo, vous avez réussi « Mois du vélo ».', '/challenges/mois-du-velo/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:51.252368', 2),
(206, 'points', '+80 points', 'Défi réussi : Mois du vélo', '/history/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:51.261082', 2),
(207, 'badge', 'Badge débloqué : Défi relevé', 'Réussir un premier défi écologique.', '/achievements/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:51.295582', 2),
(208, 'goal', 'À mi-chemin de votre objectif', 'Vous avez dépassé 50 % de votre objectif « 15 trajets à vélo ce mois-ci ». Continuez !', '/goals/1/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:51.460737', 1),
(209, 'goal', 'Objectif atteint !', 'Félicitations, vous avez atteint votre objectif « Atteindre 200 points ».', '/goals/2/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:51.500065', 1),
(210, 'goal', 'Objectif atteint !', 'Félicitations, vous avez atteint votre objectif « Trier chaque semaine ».', '/goals/3/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:51.534963', 4),
(211, 'goal', 'À mi-chemin de votre objectif', 'Vous avez dépassé 50 % de votre objectif « Réduire les veilles à zéro ». Continuez !', '/goals/4/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:51.599034', 6),
(212, 'goal', 'Objectif atteint !', 'Félicitations, vous avez atteint votre objectif « Covoiturer 3 fois ».', '/goals/11/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:51.694058', 2),
(213, 'event', 'Votre événement est publié !', '« Grand nettoyage de la plage » est désormais visible par la communauté.', '/community/grand-nettoyage-de-la-plage/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:51.823287', 4),
(214, 'event', 'Nouvel événement : Grand nettoyage de la plage', 'Le 29/10/2026 — inscrivez-vous dès maintenant.', '/community/grand-nettoyage-de-la-plage/', 1, '2026-10-24 20:32:52.688923', '2026-10-24 20:32:51.830240', 1),
(215, 'event', 'Nouvel événement : Grand nettoyage de la plage', 'Le 29/10/2026 — inscrivez-vous dès maintenant.', '/community/grand-nettoyage-de-la-plage/', 1, '2026-10-24 20:32:52.697095', '2026-10-24 20:32:51.830287', 2),
(216, 'event', 'Nouvel événement : Grand nettoyage de la plage', 'Le 29/10/2026 — inscrivez-vous dès maintenant.', '/community/grand-nettoyage-de-la-plage/', 0, NULL, '2026-10-24 20:32:51.830314', 3),
(217, 'event', 'Nouvel événement : Grand nettoyage de la plage', 'Le 29/10/2026 — inscrivez-vous dès maintenant.', '/community/grand-nettoyage-de-la-plage/', 0, NULL, '2026-10-24 20:32:51.830337', 5),
(218, 'event', 'Nouvel événement : Grand nettoyage de la plage', 'Le 29/10/2026 — inscrivez-vous dès maintenant.', '/community/grand-nettoyage-de-la-plage/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:51.830363', 6),
(219, 'event', 'Nouvel événement : Grand nettoyage de la plage', 'Le 29/10/2026 — inscrivez-vous dès maintenant.', '/community/grand-nettoyage-de-la-plage/', 0, NULL, '2026-10-24 20:32:51.830388', 7),
(220, 'event', 'Nouvel événement : Grand nettoyage de la plage', 'Le 29/10/2026 — inscrivez-vous dès maintenant.', '/community/grand-nettoyage-de-la-plage/', 0, NULL, '2026-10-24 20:32:51.830412', 8),
(221, 'event', 'Nouvel événement : Grand nettoyage de la plage', 'Le 29/10/2026 — inscrivez-vous dès maintenant.', '/community/grand-nettoyage-de-la-plage/', 1, '2026-10-24 20:32:52.741914', '2026-10-24 20:32:51.830434', 9),
(222, 'event', 'Votre événement est publié !', '« Conférence : sobriété énergétique au bureau » est désormais visible par la communauté.', '/community/conference-sobriete-energetique-au-bureau/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:51.851259', 6),
(223, 'event', 'Nouvel événement : Conférence : sobriété énergétique au bureau', 'Le 25/10/2026 — inscrivez-vous dès maintenant.', '/community/conference-sobriete-energetique-au-bureau/', 0, NULL, '2026-10-24 20:32:51.857062', 1),
(224, 'event', 'Nouvel événement : Conférence : sobriété énergétique au bureau', 'Le 25/10/2026 — inscrivez-vous dès maintenant.', '/community/conference-sobriete-energetique-au-bureau/', 0, NULL, '2026-10-24 20:32:51.857128', 2),
(225, 'event', 'Nouvel événement : Conférence : sobriété énergétique au bureau', 'Le 25/10/2026 — inscrivez-vous dès maintenant.', '/community/conference-sobriete-energetique-au-bureau/', 0, NULL, '2026-10-24 20:32:51.857172', 3),
(226, 'event', 'Nouvel événement : Conférence : sobriété énergétique au bureau', 'Le 25/10/2026 — inscrivez-vous dès maintenant.', '/community/conference-sobriete-energetique-au-bureau/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:51.857212', 4),
(227, 'event', 'Nouvel événement : Conférence : sobriété énergétique au bureau', 'Le 25/10/2026 — inscrivez-vous dès maintenant.', '/community/conference-sobriete-energetique-au-bureau/', 0, NULL, '2026-10-24 20:32:51.857253', 5),
(228, 'event', 'Nouvel événement : Conférence : sobriété énergétique au bureau', 'Le 25/10/2026 — inscrivez-vous dès maintenant.', '/community/conference-sobriete-energetique-au-bureau/', 0, NULL, '2026-10-24 20:32:51.857292', 7),
(229, 'event', 'Nouvel événement : Conférence : sobriété énergétique au bureau', 'Le 25/10/2026 — inscrivez-vous dès maintenant.', '/community/conference-sobriete-energetique-au-bureau/', 0, NULL, '2026-10-24 20:32:51.857328', 8),
(230, 'event', 'Nouvel événement : Conférence : sobriété énergétique au bureau', 'Le 25/10/2026 — inscrivez-vous dès maintenant.', '/community/conference-sobriete-energetique-au-bureau/', 0, NULL, '2026-10-24 20:32:51.857365', 9),
(231, 'event', 'Votre événement est publié !', '« Atelier compost urbain » est désormais visible par la communauté.', '/community/atelier-compost-urbain/', 0, NULL, '2026-10-24 20:32:51.878270', 9),
(232, 'event', 'Nouvel événement : Atelier compost urbain', 'Le 05/11/2026 — inscrivez-vous dès maintenant.', '/community/atelier-compost-urbain/', 0, NULL, '2026-10-24 20:32:51.884579', 1),
(233, 'event', 'Nouvel événement : Atelier compost urbain', 'Le 05/11/2026 — inscrivez-vous dès maintenant.', '/community/atelier-compost-urbain/', 0, NULL, '2026-10-24 20:32:51.884619', 2),
(234, 'event', 'Nouvel événement : Atelier compost urbain', 'Le 05/11/2026 — inscrivez-vous dès maintenant.', '/community/atelier-compost-urbain/', 0, NULL, '2026-10-24 20:32:51.884644', 3),
(235, 'event', 'Nouvel événement : Atelier compost urbain', 'Le 05/11/2026 — inscrivez-vous dès maintenant.', '/community/atelier-compost-urbain/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:51.884670', 4),
(236, 'event', 'Nouvel événement : Atelier compost urbain', 'Le 05/11/2026 — inscrivez-vous dès maintenant.', '/community/atelier-compost-urbain/', 0, NULL, '2026-10-24 20:32:51.884696', 5),
(237, 'event', 'Nouvel événement : Atelier compost urbain', 'Le 05/11/2026 — inscrivez-vous dès maintenant.', '/community/atelier-compost-urbain/', 1, '2026-10-24 20:32:52.724455', '2026-10-24 20:32:51.884721', 6),
(238, 'event', 'Nouvel événement : Atelier compost urbain', 'Le 05/11/2026 — inscrivez-vous dès maintenant.', '/community/atelier-compost-urbain/', 0, NULL, '2026-10-24 20:32:51.884745', 7),
(239, 'event', 'Nouvel événement : Atelier compost urbain', 'Le 05/11/2026 — inscrivez-vous dès maintenant.', '/community/atelier-compost-urbain/', 0, NULL, '2026-10-24 20:32:51.884769', 8),
(240, 'event', 'Nouvelle campagne : Campagne Mobilité douce', 'Le 14/10/2026 — inscrivez-vous dès maintenant.', '/community/campagne-mobilite-douce/', 0, NULL, '2026-10-24 20:32:51.910478', 1),
(241, 'event', 'Nouvelle campagne : Campagne Mobilité douce', 'Le 14/10/2026 — inscrivez-vous dès maintenant.', '/community/campagne-mobilite-douce/', 0, NULL, '2026-10-24 20:32:51.910525', 2),
(242, 'event', 'Nouvelle campagne : Campagne Mobilité douce', 'Le 14/10/2026 — inscrivez-vous dès maintenant.', '/community/campagne-mobilite-douce/', 0, NULL, '2026-10-24 20:32:51.910552', 3),
(243, 'event', 'Nouvelle campagne : Campagne Mobilité douce', 'Le 14/10/2026 — inscrivez-vous dès maintenant.', '/community/campagne-mobilite-douce/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:51.910576', 4),
(244, 'event', 'Nouvelle campagne : Campagne Mobilité douce', 'Le 14/10/2026 — inscrivez-vous dès maintenant.', '/community/campagne-mobilite-douce/', 0, NULL, '2026-10-24 20:32:51.910600', 5),
(245, 'event', 'Nouvelle campagne : Campagne Mobilité douce', 'Le 14/10/2026 — inscrivez-vous dès maintenant.', '/community/campagne-mobilite-douce/', 0, NULL, '2026-10-24 20:32:51.910626', 6),
(246, 'event', 'Nouvelle campagne : Campagne Mobilité douce', 'Le 14/10/2026 — inscrivez-vous dès maintenant.', '/community/campagne-mobilite-douce/', 0, NULL, '2026-10-24 20:32:51.910649', 7),
(247, 'event', 'Nouvelle campagne : Campagne Mobilité douce', 'Le 14/10/2026 — inscrivez-vous dès maintenant.', '/community/campagne-mobilite-douce/', 0, NULL, '2026-10-24 20:32:51.910673', 8),
(248, 'event', 'Nouvelle campagne : Campagne Mobilité douce', 'Le 14/10/2026 — inscrivez-vous dès maintenant.', '/community/campagne-mobilite-douce/', 0, NULL, '2026-10-24 20:32:51.910697', 9),
(249, 'event', 'Nouvelle inscription', 'Amina Ben Salah s’est inscrit·e à « Grand nettoyage de la plage ».', '/community/grand-nettoyage-de-la-plage/', 1, '2026-10-24 20:32:52.710930', '2026-10-24 20:32:51.941660', 4),
(250, 'badge', 'Badge débloqué : Objectif atteint', 'Atteindre un objectif personnel.', '/achievements/', 0, NULL, '2026-10-24 20:32:51.961988', 1),
(251, 'badge', 'Badge débloqué : Objectif atteint', 'Atteindre un objectif personnel.', '/achievements/', 0, NULL, '2026-10-24 20:32:52.004365', 4),
(252, 'event', 'Nouvelle inscription', 'Karim Jaziri s’est inscrit·e à « Grand nettoyage de la plage ».', '/community/grand-nettoyage-de-la-plage/', 0, NULL, '2026-10-24 20:32:52.025872', 4),
(253, 'event', 'Nouvelle inscription', 'Omar Ferchichi s’est inscrit·e à « Grand nettoyage de la plage ».', '/community/grand-nettoyage-de-la-plage/', 0, NULL, '2026-10-24 20:32:52.046722', 4),
(254, 'event', 'Nouvelle inscription', 'Nour Belhadj s’est inscrit·e à « Grand nettoyage de la plage ».', '/community/grand-nettoyage-de-la-plage/', 0, NULL, '2026-10-24 20:32:52.094759', 4),
(255, 'event', 'Nouvelle inscription', 'Mehdi Gharbi s’est inscrit·e à « Conférence : sobriété énergétique au bureau ».', '/community/conference-sobriete-energetique-au-bureau/', 0, NULL, '2026-10-24 20:32:52.170289', 6),
(256, 'event', 'Nouvelle inscription', 'Inès Chaabane s’est inscrit·e à « Conférence : sobriété énergétique au bureau ».', '/community/conference-sobriete-energetique-au-bureau/', 0, NULL, '2026-10-24 20:32:52.216541', 6),
(257, 'event', 'Nouvelle inscription', 'Lina Haddad s’est inscrit·e à « Conférence : sobriété énergétique au bureau ».', '/community/conference-sobriete-energetique-au-bureau/', 0, NULL, '2026-10-24 20:32:52.257378', 6);
INSERT INTO `notifications_notification` (`id`, `kind`, `title`, `message`, `link`, `is_read`, `read_at`, `created_at`, `recipient_id`) VALUES
(258, 'badge', 'Badge débloqué : Citoyen engagé', 'S’inscrire à 2 événements de la communauté.', '/achievements/', 0, NULL, '2026-10-24 20:32:52.275312', 4),
(259, 'event', 'Nouvelle inscription', 'Amina Ben Salah s’est inscrit·e à « Conférence : sobriété énergétique au bureau ».', '/community/conference-sobriete-energetique-au-bureau/', 0, NULL, '2026-10-24 20:32:52.297456', 6),
(260, 'badge', 'Badge débloqué : Citoyen engagé', 'S’inscrire à 2 événements de la communauté.', '/achievements/', 0, NULL, '2026-10-24 20:32:52.314044', 1),
(261, 'badge', 'Badge débloqué : Citoyen engagé', 'S’inscrire à 2 événements de la communauté.', '/achievements/', 0, NULL, '2026-10-24 20:32:52.368506', 9),
(262, 'event', 'Nouvelle inscription', 'Youssef Trabelsi s’est inscrit·e à « Atelier compost urbain ».', '/community/atelier-compost-urbain/', 0, NULL, '2026-10-24 20:32:52.399501', 9),
(263, 'badge', 'Badge débloqué : Objectif atteint', 'Atteindre un objectif personnel.', '/achievements/', 0, NULL, '2026-10-24 20:32:52.420780', 2),
(264, 'event', 'Nouvelle inscription', 'Amina Ben Salah s’est inscrit·e à « Campagne Mobilité douce ».', '/community/campagne-mobilite-douce/', 0, NULL, '2026-10-24 20:32:52.446841', 10),
(265, 'event', 'Nouvelle inscription', 'Youssef Trabelsi s’est inscrit·e à « Campagne Mobilité douce ».', '/community/campagne-mobilite-douce/', 0, NULL, '2026-10-24 20:32:52.474888', 10),
(266, 'badge', 'Badge débloqué : Citoyen engagé', 'S’inscrire à 2 événements de la communauté.', '/achievements/', 0, NULL, '2026-10-24 20:32:52.500290', 2),
(267, 'event', 'Nouvelle inscription', 'Nour Belhadj s’est inscrit·e à « Campagne Mobilité douce ».', '/community/campagne-mobilite-douce/', 0, NULL, '2026-10-24 20:32:52.532767', 10),
(268, 'badge', 'Badge débloqué : Citoyen engagé', 'S’inscrire à 2 événements de la communauté.', '/achievements/', 0, NULL, '2026-10-24 20:32:52.579196', 3),
(269, 'event', 'Nouvelle inscription', 'Mehdi Gharbi s’est inscrit·e à « Campagne Mobilité douce ».', '/community/campagne-mobilite-douce/', 0, NULL, '2026-10-24 20:32:52.636422', 10),
(270, 'badge', 'Badge débloqué : Citoyen engagé', 'S’inscrire à 2 événements de la communauté.', '/achievements/', 0, NULL, '2026-10-24 20:32:52.678161', 7),
(271, 'event', 'Bientôt : Conférence : sobriété énergétique au bureau', 'Rendez-vous le 25/10/2026 à 18:00.', '/community/conference-sobriete-energetique-au-bureau/', 0, NULL, '2026-10-24 20:56:26.822639', 1),
(272, 'event', 'Bientôt : Conférence : sobriété énergétique au bureau', 'Rendez-vous le 25/10/2026 à 18:00.', '/community/conference-sobriete-energetique-au-bureau/', 0, NULL, '2026-10-24 21:04:04.220826', 4);

-- --------------------------------------------------------

--
-- Structure de la table `notifications_notificationpreference`
--

CREATE TABLE `notifications_notificationpreference` (
  `id` bigint(20) NOT NULL,
  `team` tinyint(1) NOT NULL,
  `challenge` tinyint(1) NOT NULL,
  `action` tinyint(1) NOT NULL,
  `points` tinyint(1) NOT NULL,
  `badge` tinyint(1) NOT NULL,
  `goal` tinyint(1) NOT NULL,
  `event` tinyint(1) NOT NULL,
  `leaderboard` tinyint(1) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `teams_membership`
--

CREATE TABLE `teams_membership` (
  `id` bigint(20) NOT NULL,
  `role` varchar(20) NOT NULL,
  `joined_at` datetime(6) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `team_id` bigint(20) NOT NULL,
  `captain_of` bigint(20) UNSIGNED DEFAULT NULL CHECK (`captain_of` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `teams_membership`
--

INSERT INTO `teams_membership` (`id`, `role`, `joined_at`, `user_id`, `team_id`, `captain_of`) VALUES
(1, 'captain', '2026-09-24 10:38:00.000000', 1, 1, 1),
(2, 'member', '2026-09-26 12:39:00.000000', 2, 1, NULL),
(3, 'member', '2026-09-27 12:26:00.000000', 3, 1, NULL),
(4, 'captain', '2026-09-24 10:53:00.000000', 4, 2, 2),
(5, 'member', '2026-09-26 12:46:00.000000', 5, 2, NULL),
(6, 'captain', '2026-09-24 10:48:00.000000', 6, 3, 3),
(7, 'member', '2026-09-26 12:49:00.000000', 7, 3, NULL),
(8, 'member', '2026-09-27 12:28:00.000000', 8, 3, NULL),
(9, 'captain', '2026-09-24 10:05:00.000000', 9, 4, 4),
(10, 'captain', '2026-09-24 10:52:00.000000', 10, 5, 5);

-- --------------------------------------------------------

--
-- Structure de la table `teams_team`
--

CREATE TABLE `teams_team` (
  `id` bigint(20) NOT NULL,
  `name` varchar(80) NOT NULL,
  `slug` varchar(90) NOT NULL,
  `description` longtext NOT NULL,
  `motto` varchar(140) NOT NULL,
  `logo` varchar(100) NOT NULL,
  `focus_area` varchar(20) NOT NULL,
  `status` varchar(20) NOT NULL,
  `is_open` tinyint(1) NOT NULL,
  `max_members` smallint(5) UNSIGNED NOT NULL CHECK (`max_members` >= 0),
  `goal_points` int(10) UNSIGNED DEFAULT NULL CHECK (`goal_points` >= 0),
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `captain_id` bigint(20) NOT NULL
) ;

--
-- Déchargement des données de la table `teams_team`
--

INSERT INTO `teams_team` (`id`, `name`, `slug`, `description`, `motto`, `logo`, `focus_area`, `status`, `is_open`, `max_members`, `goal_points`, `created_at`, `updated_at`, `captain_id`) VALUES
(1, 'Les Pédaleurs Verts', 'les-pedaleurs-verts', 'Équipe de démonstration d’étudiants qui privilégient le vélo et les transports en commun.', 'Chaque coup de pédale compte.', '', 'transport', 'active', 1, 6, 600, '2026-09-24 10:14:00.000000', '2026-10-24 20:32:42.424842', 1),
(2, 'Zéro Déchet Squad', 'zero-dechet-squad', 'Équipe de démonstration de salariés engagés dans le tri, la réparation et le réemploi.', 'Moins jeter, mieux trier.', '', 'recycling', 'active', 1, 6, 500, '2026-09-24 10:36:00.000000', '2026-10-24 20:32:42.521169', 4),
(3, 'Watt Watchers', 'watt-watchers', 'Équipe associative de démonstration qui traque le gaspillage d’énergie.', 'Le meilleur kWh est celui qu’on ne consomme pas.', '', 'energy', 'active', 1, 6, NULL, '2026-09-24 10:49:00.000000', '2026-10-24 20:32:42.547651', 6),
(4, 'Gouttes d’Avenir', 'gouttes-davenir', 'Équipe de démonstration dédiée aux économies d’eau.', 'Préserver chaque goutte.', '', 'water', 'active', 1, 6, NULL, '2026-09-24 10:00:00.000000', '2026-10-24 20:32:42.574175', 9),
(5, 'Consom’Acteurs', 'consomacteurs', 'Équipe de démonstration qui promeut le réemploi et la consommation responsable.', 'Consommer moins, consommer mieux.', '', 'consumption', 'active', 1, 6, 400, '2026-09-24 10:07:00.000000', '2026-10-24 20:32:42.589544', 10);

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `accounts_role`
--
ALTER TABLE `accounts_role`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `group_id` (`group_id`);

--
-- Index pour la table `accounts_user`
--
ALTER TABLE `accounts_user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Index pour la table `accounts_user_groups`
--
ALTER TABLE `accounts_user_groups`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `accounts_user_groups_user_id_group_id_59c0b32f_uniq` (`user_id`,`group_id`),
  ADD KEY `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` (`group_id`);

--
-- Index pour la table `accounts_user_user_permissions`
--
ALTER TABLE `accounts_user_user_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `accounts_user_user_permi_user_id_permission_id_2ab516c2_uniq` (`user_id`,`permission_id`),
  ADD KEY `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` (`permission_id`);

--
-- Index pour la table `actions_actionsubmission`
--
ALTER TABLE `actions_actionsubmission`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `actions_actionsubmission_dedupe_key_491843f3_uniq` (`dedupe_key`),
  ADD KEY `actions_act_user_id_40fff3_idx` (`user_id`,`status`),
  ADD KEY `actions_act_status_18a9b6_idx` (`status`,`created_at`),
  ADD KEY `actions_act_team_id_8024c1_idx` (`team_id`,`status`),
  ADD KEY `actions_actionsubmis_challenge_id_04027de7_fk_challenge` (`challenge_id`),
  ADD KEY `actions_actionsubmis_reviewed_by_id_929204a4_fk_accounts_` (`reviewed_by_id`),
  ADD KEY `actions_actionsubmis_action_type_id_3d0245aa_fk_actions_e` (`action_type_id`);

--
-- Index pour la table `actions_ecoactiontype`
--
ALTER TABLE `actions_ecoactiontype`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD UNIQUE KEY `slug` (`slug`),
  ADD KEY `actions_eco_is_acti_f5a6c6_idx` (`is_active`,`category`);

--
-- Index pour la table `actions_moderationlog`
--
ALTER TABLE `actions_moderationlog`
  ADD PRIMARY KEY (`id`),
  ADD KEY `actions_moderationlog_moderator_id_237aa373_fk_accounts_user_id` (`moderator_id`),
  ADD KEY `actions_moderationlo_submission_id_553e04b9_fk_actions_a` (`submission_id`);

--
-- Index pour la table `analytics_activitylog`
--
ALTER TABLE `analytics_activitylog`
  ADD PRIMARY KEY (`id`),
  ADD KEY `analytics_activitylog_created_at_045d2982` (`created_at`),
  ADD KEY `analytics_a_actor_i_efaf6c_idx` (`actor_id`,`created_at`),
  ADD KEY `analytics_a_team_id_4f6d58_idx` (`team_id`,`created_at`);

--
-- Index pour la table `auth_group`
--
ALTER TABLE `auth_group`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Index pour la table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  ADD KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`);

--
-- Index pour la table `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`);

--
-- Index pour la table `challenges_challenge`
--
ALTER TABLE `challenges_challenge`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `slug` (`slug`),
  ADD KEY `challenges__status_8d928f_idx` (`status`,`category`),
  ADD KEY `challenges__start_d_a588ff_idx` (`start_date`,`end_date`),
  ADD KEY `challenges_challenge_creator_id_e2660898_fk_accounts_user_id` (`creator_id`),
  ADD KEY `challenges_challenge_reviewed_by_id_78e28577_fk_accounts_user_id` (`reviewed_by_id`);

--
-- Index pour la table `challenges_challengeparticipation`
--
ALTER TABLE `challenges_challengeparticipation`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_challenge_participation` (`challenge_id`,`user_id`),
  ADD KEY `challenges__user_id_104bf1_idx` (`user_id`,`status`),
  ADD KEY `challenges__team_id_77d520_idx` (`team_id`,`status`);

--
-- Index pour la table `community_event`
--
ALTER TABLE `community_event`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `slug` (`slug`),
  ADD KEY `community_e_status_a1540c_idx` (`status`,`start_at`),
  ADD KEY `community_event_organizer_id_3d0bb70c_fk_accounts_user_id` (`organizer_id`),
  ADD KEY `community_event_reviewed_by_id_ee13b226_fk_accounts_user_id` (`reviewed_by_id`);

--
-- Index pour la table `community_eventparticipation`
--
ALTER TABLE `community_eventparticipation`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_event_participation` (`event_id`,`user_id`),
  ADD KEY `community_eventparticipation_team_id_4a2d953e_fk_teams_team_id` (`team_id`),
  ADD KEY `community_eventparti_user_id_f100162f_fk_accounts_` (`user_id`);

--
-- Index pour la table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  ADD KEY `django_admin_log_user_id_c564eba6_fk_accounts_user_id` (`user_id`);

--
-- Index pour la table `django_content_type`
--
ALTER TABLE `django_content_type`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`);

--
-- Index pour la table `django_migrations`
--
ALTER TABLE `django_migrations`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `django_session`
--
ALTER TABLE `django_session`
  ADD PRIMARY KEY (`session_key`),
  ADD KEY `django_session_expire_date_a5c62663` (`expire_date`);

--
-- Index pour la table `gamification_badge`
--
ALTER TABLE `gamification_badge`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD UNIQUE KEY `slug` (`slug`);

--
-- Index pour la table `gamification_pointtransaction`
--
ALTER TABLE `gamification_pointtransaction`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `reference` (`reference`),
  ADD KEY `gamification_pointtr_challenge_id_79d6f274_fk_challenge` (`challenge_id`),
  ADD KEY `gamification_pointtr_created_by_id_117d6aef_fk_accounts_` (`created_by_id`),
  ADD KEY `gamification_pointtr_submission_id_8073138b_fk_actions_a` (`submission_id`),
  ADD KEY `gamification_pointtransaction_created_at_e4eb1d11` (`created_at`),
  ADD KEY `gamificatio_user_id_d3e19d_idx` (`user_id`,`created_at`),
  ADD KEY `gamificatio_team_id_f9ad44_idx` (`team_id`,`created_at`);

--
-- Index pour la table `gamification_userbadge`
--
ALTER TABLE `gamification_userbadge`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_user_badge` (`user_id`,`badge_id`),
  ADD KEY `gamification_userbad_badge_id_d544c9cb_fk_gamificat` (`badge_id`);

--
-- Index pour la table `goals_goal`
--
ALTER TABLE `goals_goal`
  ADD PRIMARY KEY (`id`),
  ADD KEY `goals_goal_user_id_7ad9fc_idx` (`user_id`,`status`);

--
-- Index pour la table `notifications_notification`
--
ALTER TABLE `notifications_notification`
  ADD PRIMARY KEY (`id`),
  ADD KEY `notificatio_recipie_86ea8b_idx` (`recipient_id`,`is_read`,`created_at`);

--
-- Index pour la table `notifications_notificationpreference`
--
ALTER TABLE `notifications_notificationpreference`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`);

--
-- Index pour la table `teams_membership`
--
ALTER TABLE `teams_membership`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `one_team_per_user` (`user_id`),
  ADD UNIQUE KEY `teams_membership_captain_of_b3d0f75b_uniq` (`captain_of`),
  ADD KEY `teams_membership_team_id_d18da3f9_fk_teams_team_id` (`team_id`);

--
-- Index pour la table `teams_team`
--
ALTER TABLE `teams_team`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD UNIQUE KEY `slug` (`slug`),
  ADD KEY `teams_team_status_764c9d_idx` (`status`,`focus_area`),
  ADD KEY `teams_team_captain_id_4934c986_fk_accounts_user_id` (`captain_id`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `accounts_role`
--
ALTER TABLE `accounts_role`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT pour la table `accounts_user`
--
ALTER TABLE `accounts_user`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT pour la table `accounts_user_groups`
--
ALTER TABLE `accounts_user_groups`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT pour la table `accounts_user_user_permissions`
--
ALTER TABLE `accounts_user_user_permissions`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `actions_actionsubmission`
--
ALTER TABLE `actions_actionsubmission`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=59;

--
-- AUTO_INCREMENT pour la table `actions_ecoactiontype`
--
ALTER TABLE `actions_ecoactiontype`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `actions_moderationlog`
--
ALTER TABLE `actions_moderationlog`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=55;

--
-- AUTO_INCREMENT pour la table `analytics_activitylog`
--
ALTER TABLE `analytics_activitylog`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=224;

--
-- AUTO_INCREMENT pour la table `auth_group`
--
ALTER TABLE `auth_group`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT pour la table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT pour la table `auth_permission`
--
ALTER TABLE `auth_permission`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=98;

--
-- AUTO_INCREMENT pour la table `challenges_challenge`
--
ALTER TABLE `challenges_challenge`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `challenges_challengeparticipation`
--
ALTER TABLE `challenges_challengeparticipation`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;

--
-- AUTO_INCREMENT pour la table `community_event`
--
ALTER TABLE `community_event`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `community_eventparticipation`
--
ALTER TABLE `community_eventparticipation`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;

--
-- AUTO_INCREMENT pour la table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `django_content_type`
--
ALTER TABLE `django_content_type`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- AUTO_INCREMENT pour la table `django_migrations`
--
ALTER TABLE `django_migrations`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=31;

--
-- AUTO_INCREMENT pour la table `gamification_badge`
--
ALTER TABLE `gamification_badge`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `gamification_pointtransaction`
--
ALTER TABLE `gamification_pointtransaction`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `gamification_userbadge`
--
ALTER TABLE `gamification_userbadge`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=38;

--
-- AUTO_INCREMENT pour la table `goals_goal`
--
ALTER TABLE `goals_goal`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `notifications_notification`
--
ALTER TABLE `notifications_notification`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=273;

--
-- AUTO_INCREMENT pour la table `notifications_notificationpreference`
--
ALTER TABLE `notifications_notificationpreference`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `teams_membership`
--
ALTER TABLE `teams_membership`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT pour la table `teams_team`
--
ALTER TABLE `teams_team`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `accounts_role`
--
ALTER TABLE `accounts_role`
  ADD CONSTRAINT `accounts_role_group_id_b152f7d6_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);

--
-- Contraintes pour la table `accounts_user_groups`
--
ALTER TABLE `accounts_user_groups`
  ADD CONSTRAINT `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  ADD CONSTRAINT `accounts_user_groups_user_id_52b62117_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`);

--
-- Contraintes pour la table `accounts_user_user_permissions`
--
ALTER TABLE `accounts_user_user_permissions`
  ADD CONSTRAINT `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `accounts_user_user_p_user_id_e4f0a161_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`);

--
-- Contraintes pour la table `actions_actionsubmission`
--
ALTER TABLE `actions_actionsubmission`
  ADD CONSTRAINT `actions_actionsubmis_action_type_id_3d0245aa_fk_actions_e` FOREIGN KEY (`action_type_id`) REFERENCES `actions_ecoactiontype` (`id`),
  ADD CONSTRAINT `actions_actionsubmis_challenge_id_04027de7_fk_challenge` FOREIGN KEY (`challenge_id`) REFERENCES `challenges_challenge` (`id`),
  ADD CONSTRAINT `actions_actionsubmis_reviewed_by_id_929204a4_fk_accounts_` FOREIGN KEY (`reviewed_by_id`) REFERENCES `accounts_user` (`id`),
  ADD CONSTRAINT `actions_actionsubmission_team_id_7e552434_fk_teams_team_id` FOREIGN KEY (`team_id`) REFERENCES `teams_team` (`id`),
  ADD CONSTRAINT `actions_actionsubmission_user_id_4906406e_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`);

--
-- Contraintes pour la table `actions_moderationlog`
--
ALTER TABLE `actions_moderationlog`
  ADD CONSTRAINT `actions_moderationlo_submission_id_553e04b9_fk_actions_a` FOREIGN KEY (`submission_id`) REFERENCES `actions_actionsubmission` (`id`),
  ADD CONSTRAINT `actions_moderationlog_moderator_id_237aa373_fk_accounts_user_id` FOREIGN KEY (`moderator_id`) REFERENCES `accounts_user` (`id`);

--
-- Contraintes pour la table `analytics_activitylog`
--
ALTER TABLE `analytics_activitylog`
  ADD CONSTRAINT `analytics_activitylog_actor_id_ce316cff_fk_accounts_user_id` FOREIGN KEY (`actor_id`) REFERENCES `accounts_user` (`id`),
  ADD CONSTRAINT `analytics_activitylog_team_id_2a745c04_fk_teams_team_id` FOREIGN KEY (`team_id`) REFERENCES `teams_team` (`id`);

--
-- Contraintes pour la table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);

--
-- Contraintes pour la table `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);

--
-- Contraintes pour la table `challenges_challenge`
--
ALTER TABLE `challenges_challenge`
  ADD CONSTRAINT `challenges_challenge_creator_id_e2660898_fk_accounts_user_id` FOREIGN KEY (`creator_id`) REFERENCES `accounts_user` (`id`),
  ADD CONSTRAINT `challenges_challenge_reviewed_by_id_78e28577_fk_accounts_user_id` FOREIGN KEY (`reviewed_by_id`) REFERENCES `accounts_user` (`id`);

--
-- Contraintes pour la table `challenges_challengeparticipation`
--
ALTER TABLE `challenges_challengeparticipation`
  ADD CONSTRAINT `challenges_challenge_challenge_id_ec1bda8b_fk_challenge` FOREIGN KEY (`challenge_id`) REFERENCES `challenges_challenge` (`id`),
  ADD CONSTRAINT `challenges_challenge_team_id_a50eaeb7_fk_teams_tea` FOREIGN KEY (`team_id`) REFERENCES `teams_team` (`id`),
  ADD CONSTRAINT `challenges_challenge_user_id_eb628f4a_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`);

--
-- Contraintes pour la table `community_event`
--
ALTER TABLE `community_event`
  ADD CONSTRAINT `community_event_organizer_id_3d0bb70c_fk_accounts_user_id` FOREIGN KEY (`organizer_id`) REFERENCES `accounts_user` (`id`),
  ADD CONSTRAINT `community_event_reviewed_by_id_ee13b226_fk_accounts_user_id` FOREIGN KEY (`reviewed_by_id`) REFERENCES `accounts_user` (`id`);

--
-- Contraintes pour la table `community_eventparticipation`
--
ALTER TABLE `community_eventparticipation`
  ADD CONSTRAINT `community_eventparti_event_id_9fd63450_fk_community` FOREIGN KEY (`event_id`) REFERENCES `community_event` (`id`),
  ADD CONSTRAINT `community_eventparti_user_id_f100162f_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`),
  ADD CONSTRAINT `community_eventparticipation_team_id_4a2d953e_fk_teams_team_id` FOREIGN KEY (`team_id`) REFERENCES `teams_team` (`id`);

--
-- Contraintes pour la table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  ADD CONSTRAINT `django_admin_log_user_id_c564eba6_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`);

--
-- Contraintes pour la table `gamification_pointtransaction`
--
ALTER TABLE `gamification_pointtransaction`
  ADD CONSTRAINT `gamification_pointtr_challenge_id_79d6f274_fk_challenge` FOREIGN KEY (`challenge_id`) REFERENCES `challenges_challenge` (`id`),
  ADD CONSTRAINT `gamification_pointtr_created_by_id_117d6aef_fk_accounts_` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  ADD CONSTRAINT `gamification_pointtr_submission_id_8073138b_fk_actions_a` FOREIGN KEY (`submission_id`) REFERENCES `actions_actionsubmission` (`id`),
  ADD CONSTRAINT `gamification_pointtr_user_id_4f6b3892_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`),
  ADD CONSTRAINT `gamification_pointtransaction_team_id_fe1fc354_fk_teams_team_id` FOREIGN KEY (`team_id`) REFERENCES `teams_team` (`id`);

--
-- Contraintes pour la table `gamification_userbadge`
--
ALTER TABLE `gamification_userbadge`
  ADD CONSTRAINT `gamification_userbad_badge_id_d544c9cb_fk_gamificat` FOREIGN KEY (`badge_id`) REFERENCES `gamification_badge` (`id`),
  ADD CONSTRAINT `gamification_userbadge_user_id_6f451a69_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`);

--
-- Contraintes pour la table `goals_goal`
--
ALTER TABLE `goals_goal`
  ADD CONSTRAINT `goals_goal_user_id_31fcb355_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`);

--
-- Contraintes pour la table `notifications_notification`
--
ALTER TABLE `notifications_notification`
  ADD CONSTRAINT `notifications_notifi_recipient_id_d055f3f0_fk_accounts_` FOREIGN KEY (`recipient_id`) REFERENCES `accounts_user` (`id`);

--
-- Contraintes pour la table `notifications_notificationpreference`
--
ALTER TABLE `notifications_notificationpreference`
  ADD CONSTRAINT `notifications_notifi_user_id_7cfb3d3a_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`);

--
-- Contraintes pour la table `teams_membership`
--
ALTER TABLE `teams_membership`
  ADD CONSTRAINT `teams_membership_team_id_d18da3f9_fk_teams_team_id` FOREIGN KEY (`team_id`) REFERENCES `teams_team` (`id`),
  ADD CONSTRAINT `teams_membership_user_id_b6b997fa_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`);

--
-- Contraintes pour la table `teams_team`
--
ALTER TABLE `teams_team`
  ADD CONSTRAINT `teams_team_captain_id_4934c986_fk_accounts_user_id` FOREIGN KEY (`captain_id`) REFERENCES `accounts_user` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
