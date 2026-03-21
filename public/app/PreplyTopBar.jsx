"use client";

import styled from "styled-components";
import {
  Wallet, ChevronDown, CalendarClock, HelpCircle, Bell, User,
} from "lucide-react";

const TopBarWrap = styled.div`
  background: #fff;
  border-bottom: 1px solid #efeef3;
  padding: 24px 32px;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const TopBarLabel = styled.span`
  font-weight: 600;
  font-size: 15px;
  color: #111827;
`;

const TopBarBadge = styled.span`
  background: #fef3c7;
  color: #92400e;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
`;

const TopBarRight = styled.div`
  display: flex;
  align-items: center;
  gap: 20px;
  margin-left: auto;
`;

const BalanceItem = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: "PreplyInter", sans-serif;
  font-size: 15px;
  font-weight: 400;
  color: #111827;
`;

const EarnButton = styled.button`
  background: #fff;
  border: 1.5px solid #d1d5db;
  border-radius: 8px;
  padding: 8px 20px;
  font-family: "PreplyInter", sans-serif;
  font-size: 15px;
  font-weight: 400;
  color: #111827;
  cursor: pointer;
  transition: border-color 0.15s;

  &:hover {
    border-color: #9ca3af;
  }
`;

const LangSelector = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
  font-family: "PreplyInter", sans-serif;
  font-size: 15px;
  font-weight: 400;
  color: #111827;
  cursor: pointer;
`;

const IconButton = styled.button`
  position: relative;
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: #111827;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const BadgeCount = styled.span`
  position: absolute;
  top: -4px;
  right: -6px;
  background: #111827;
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  min-width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 3px;
`;

const AvatarSquare = styled.div`
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: rgba(0, 0, 0, 0.25);
`;

const NavBar = styled.nav`
  background: #fff;
  padding: 0 32px;
  display: flex;
  align-items: stretch;
  gap: 0;
  border-bottom: 1px solid #e5e7eb;
  overflow-x: auto;
`;

const NavItem = styled.a`
  font-family: inherit;
  font-size: 14px;
  font-weight: ${(props) => (props.$active ? "600" : "500")};
  color: ${(props) => (props.$active ? "#111827" : "#6b7280")};
  padding: 14px 16px;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
  position: relative;
  transition: color 0.15s;
  letter-spacing: 0.04em;

  &::after {
    content: "";
    position: absolute;
    bottom: 0;
    left: 16px;
    right: 16px;
    height: 4px;
    border-radius: 1px;
    background: ${(props) => (props.$active ? "#ff7aac" : "transparent")};
  }

  &:hover {
    color: #111827;
  }
`;

export default function PreplyTopBar() {
  return (
    <>
      <TopBarWrap>
        <TopBarLabel>
          <img src="/preply.svg" alt="Preply" />
        </TopBarLabel>
        <TopBarBadge>Hackathon submission</TopBarBadge>

        <TopBarRight>
          <BalanceItem>
            <Wallet size={20} />
            0.00 USD
          </BalanceItem>
          <EarnButton>Earn $25</EarnButton>
          <LangSelector>
            English, USD
            <ChevronDown size={18} />
          </LangSelector>
          <IconButton>
            <CalendarClock size={22} />
            <BadgeCount>0</BadgeCount>
          </IconButton>
          <IconButton>
            <HelpCircle size={22} />
          </IconButton>
          <IconButton>
            <Bell size={22} />
          </IconButton>
          <AvatarSquare><User size={20} /></AvatarSquare>
        </TopBarRight>
      </TopBarWrap>

      <NavBar>
        <NavItem href="#">Home</NavItem>
        <NavItem href="#">Messages</NavItem>
        <NavItem href="#">Calendar</NavItem>
        <NavItem href="#">Students</NavItem>
        <NavItem href="#">Classroom</NavItem>
        <NavItem href="#">Insights</NavItem>
        <NavItem href="#">My profile</NavItem>
        <NavItem href="#">Settings</NavItem>
        <NavItem href="#">Academy</NavItem>
        <NavItem href="#">Community</NavItem>
        <NavItem href="#" $active>Teacher Dashboard</NavItem>
      </NavBar>
    </>
  );
}
