using LiskovDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static void Main(){

 foreach(IWithdrawable a in new IWithdrawable[]{new CheckingAccount("a",100),new LimitedCheckingAccount("b",100,20)}){
  decimal before=a.Balance;Throws<ArgumentOutOfRangeException>(()=>a.TryWithdraw(-1,out _));Check(a.Balance==before,"negative unchanged");
  Check(!a.TryWithdraw(101,out _) && a.Balance==before,"over balance unchanged");
  bool ok=a.TryWithdraw(50,out string reason);Check(a.Balance==(ok?before-50:before) && reason.Length>0,"shared success/failure postcondition");
 }
 var evil=new ProbeAccount();Throws<ArgumentOutOfRangeException>(()=>evil.Debit(-1));Check(evil.Balance==10,"protected guard");
 var first=new BankAccount("a",100);Throws<NotSupportedException>(()=>MonthlyFeeJob.Run(new BankAccount[]{first,new FixedDepositAccount("b",100)},10));Check(first.Balance==90,"legacy partial effect");

 }
 sealed class ProbeAccount():AccountBase("a",10) {public bool Debit(decimal a)=>TryDebit(a);}
}
