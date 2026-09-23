
internal static class Contracts
{
 static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
 public static void Main(){
var a=new BankAccount("A",10m);var b=new BankAccount("B",decimal.MaxValue);
Throws<OverflowException>(()=>a.TransferTo(b,1m));Check(a.Balance==10m && b.Balance==decimal.MaxValue,"overflow changed account");
Throws<InvalidOperationException>(()=>a.TransferTo(a,1m));Throws<ArgumentOutOfRangeException>(()=>a.TransferTo(b,0m));
var c=new BankAccount("C",0m);a.TransferTo(c,7m);Check(a.Balance==3m && c.Balance==7m,"transfer conservation");
Throws<InvalidOperationException>(()=>a.TransferTo(c,4m));Check(a.Balance==3m && c.Balance==7m,"overdraw mutation");
Throws<InvalidOperationException>(()=>a.TransferTo(new BankAccount("USD",0m,"USD"),1m));
 }
}
